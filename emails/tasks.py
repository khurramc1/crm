import json
from datetime import datetime, timedelta
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings

from .models import Campaign, EmailLog, EmailTemplate
from contacts.models import Contact


@shared_task
def send_email_task(email_log_id):
    """
    Send a single email using SendGrid API
    """
    try:
        email_log = EmailLog.objects.get(id=email_log_id)
        contact = email_log.contact
        template = email_log.template
        
        if not template:
            email_log.status = 'failed'
            email_log.error_message = 'No template found'
            email_log.save()
            return
        
        # Render template with merge tags
        merge_tags = {
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'full_name': contact.full_name,
            'email': contact.email,
            'phone': contact.phone or '',
            'company_name': contact.company.name if contact.company else '',
        }
        
        # Simple template rendering (replace {{key}} with values)
        rendered_subject = template.subject
        rendered_html = template.html_body
        
        for key, value in merge_tags.items():
            rendered_subject = rendered_subject.replace(f'{{{{{key}}}}}', str(value))
            rendered_html = rendered_html.replace(f'{{{{{key}}}}}', str(value))
        
        # Add tracking pixel to HTML
        tracking_pixel = f'<img src="/track/open/{email_log.id}/" width="1" height="1" style="display:none;">'
        rendered_html = rendered_html.replace('</body>', f'{tracking_pixel}</body>')
        
        # Store rendered content
        email_log.rendered_subject = rendered_subject
        email_log.rendered_html = rendered_html
        
        if settings.SENDGRID_API_KEY:
            # Send via SendGrid
            message = Mail(
                from_email=(template.from_email or settings.DEFAULT_FROM_EMAIL),
                to_emails=contact.email,
                subject=rendered_subject,
                html_content=rendered_html,
                plain_text_content=template.plain_body or ''
            )
            
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                email_log.status = 'sent'
                email_log.sent_at = timezone.now()
                email_log.email_id = response.headers.get('X-Message-Id', '')
            else:
                email_log.status = 'failed'
                email_log.error_message = f'SendGrid error: {response.status_code}'
        else:
            # Use Django email backend (console or SMTP)
            send_mail(
                rendered_subject,
                template.plain_body or '',
                settings.DEFAULT_FROM_EMAIL,
                [contact.email],
                html_message=rendered_html,
                fail_silently=False,
            )
            
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
        
        email_log.save()
        
        # Update campaign stats
        if email_log.campaign:
            campaign = email_log.campaign
            campaign.sent_count = EmailLog.objects.filter(
                campaign=campaign,
                status__in=['sent', 'delivered']
            ).count()
            campaign.save()
        
        return f"Email sent to {contact.email}"
        
    except Exception as e:
        email_log.status = 'failed'
        email_log.error_message = str(e)
        email_log.save()
        raise


@shared_task
def process_campaign(campaign_id):
    """
    Process a campaign: create EmailLog entries for each contact
    and queue send tasks
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        
        if campaign.status not in ['draft', 'scheduled']:
            return f"Campaign {campaign_id} is not in draft or scheduled state"
        
        campaign.status = 'sending'
        campaign.started_at = timezone.now()
        campaign.save()
        
        # Get contacts based on segment filter
        contacts = Contact.objects.all()
        
        if campaign.segment_filter:
            try:
                filters = json.loads(campaign.segment_filter)
                if 'status' in filters:
                    contacts = contacts.filter(status=filters['status'])
                if 'tags' in filters:
                    contacts = contacts.filter(tags__icontains=filters['tags'])
            except json.JSONDecodeError:
                pass
        
        # Create EmailLog entries and queue sends
        for contact in contacts:
            email_log, created = EmailLog.objects.get_or_create(
                contact=contact,
                campaign=campaign,
                template=campaign.template,
                defaults={'status': 'pending'}
            )
            
            if created or email_log.status == 'pending':
                # Queue the send task
                send_email_task.delay(email_log.id)
        
        return f"Campaign {campaign_id} queued for sending"
        
    except Exception as e:
        campaign = Campaign.objects.get(id=campaign_id)
        campaign.status = 'draft'
        campaign.save()
        raise


@shared_task
def process_scheduled_campaigns():
    """
    Process campaigns that are scheduled to send now
    Runs every minute via Celery Beat
    """
    now = timezone.now()
    
    scheduled_campaigns = Campaign.objects.filter(
        status='scheduled',
        scheduled_at__lte=now
    )
    
    for campaign in scheduled_campaigns:
        process_campaign.delay(campaign.id)
    
    return f"Processed {scheduled_campaigns.count()} scheduled campaigns"
