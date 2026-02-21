from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from contacts.models import Contact, Company
from deals.models import Pipeline, Stage, Deal
from emails.models import EmailTemplate, Campaign
from automations.models import Workflow, WorkflowStep
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / admin123'))

        # Create sample companies
        companies = []
        company_data = [
            {'name': 'Acme Corp', 'domain': 'acme.com', 'industry': 'Technology', 'size': '51-200'},
            {'name': 'TechStart Inc', 'domain': 'techstart.com', 'industry': 'Software', 'size': '11-50'},
            {'name': 'Global Solutions', 'domain': 'globalsol.com', 'industry': 'Consulting', 'size': '201-500'},
        ]
        
        for data in company_data:
            company, created = Company.objects.get_or_create(
                name=data['name'],
                defaults={'domain': data['domain'], 'industry': data['industry'], 'size': data['size']}
            )
            companies.append(company)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created company: {company.name}'))

        # Create sample contacts
        admin = User.objects.get(username='admin')
        contact_data = [
            {'first_name': 'John', 'last_name': 'Doe', 'email': 'john@acme.com', 'company': companies[0]},
            {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane@techstart.com', 'company': companies[1]},
            {'first_name': 'Bob', 'last_name': 'Johnson', 'email': 'bob@globalsol.com', 'company': companies[2]},
        ]
        
        contacts = []
        for data in contact_data:
            contact, created = Contact.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'company': data['company'],
                    'status': 'lead',
                    'assigned_to': admin,
                    'tags': 'important,sales'
                }
            )
            contacts.append(contact)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created contact: {contact.full_name}'))

        # Create email template
        template, created = EmailTemplate.objects.get_or_create(
            name='Welcome Email',
            defaults={
                'subject': 'Welcome to CRM, {{first_name}}!',
                'html_body': '''<html>
<body>
    <p>Hi {{first_name}},</p>
    <p>Welcome to our CRM system. We're excited to work with {{company_name}}.</p>
    <p>Best regards,<br>The Team</p>
</body>
</html>''',
                'plain_body': 'Hi {{first_name}}, Welcome to our CRM system.',
                'created_by': admin,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created email template: Welcome Email'))

        # Create pipeline
        pipeline, created = Pipeline.objects.get_or_create(
            name='Standard Pipeline',
            defaults={'description': 'Standard sales pipeline', 'created_by': admin}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created pipeline: Standard Pipeline'))

        # Create stages
        stages_data = [
            {'name': 'Lead', 'order': 1, 'probability': 10},
            {'name': 'Qualified', 'order': 2, 'probability': 25},
            {'name': 'Proposal', 'order': 3, 'probability': 50},
            {'name': 'Negotiation', 'order': 4, 'probability': 75},
            {'name': 'Closed Won', 'order': 5, 'probability': 100},
        ]
        
        for stage_data in stages_data:
            stage, created = Stage.objects.get_or_create(
                name=stage_data['name'],
                pipeline=pipeline,
                defaults={'order': stage_data['order'], 'probability': stage_data['probability']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created stage: {stage.name}'))

        # Create sample deals
        first_stage = pipeline.stages.first()
        for i, contact in enumerate(contacts):
            deal, created = Deal.objects.get_or_create(
                title=f'Deal with {contact.company.name}',
                contact=contact,
                defaults={
                    'value': (i + 1) * 50000,
                    'pipeline': pipeline,
                    'stage': first_stage,
                    'assigned_to': admin,
                    'close_date': timezone.now().date() + timedelta(days=30),
                    'status': 'open',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created deal: {deal.title}'))

        # Create workflow
        workflow, created = Workflow.objects.get_or_create(
            name='New Contact Workflow',
            defaults={
                'description': 'Automated workflow for new contacts',
                'trigger_event': 'contact_created',
                'is_active': True,
                'created_by': admin,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created workflow: New Contact Workflow'))

        # Create workflow steps
        step_data = [
            {'order': 1, 'action': 'send_email', 'delay_days': 0},
            {'order': 2, 'action': 'add_tag', 'delay_days': 3, 'action_data': '{"tag": "contacted"}'},
        ]
        
        for data in step_data:
            step, created = WorkflowStep.objects.get_or_create(
                workflow=workflow,
                order=data['order'],
                defaults={
                    'action': data['action'],
                    'delay_days': data['delay_days'],
                    'email_template': template if data['action'] == 'send_email' else None,
                    'action_data': data.get('action_data', ''),
                    'is_enabled': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created workflow step: {step.action}'))

        self.stdout.write(self.style.SUCCESS('Sample data populated successfully!'))
