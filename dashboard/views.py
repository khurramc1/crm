from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta

from contacts.models import Contact
from deals.models import Deal
from emails.models import Campaign, EmailLog
from automations.models import WorkflowExecution


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard with overview stats"""
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Basic stats
        context['total_contacts'] = Contact.objects.count()
        context['total_companies'] = Contact.objects.values('company').distinct().count()
        context['active_deals'] = Deal.objects.filter(status='open').count()
        context['total_deal_value'] = sum(
            d.value for d in Deal.objects.filter(status='open')
        )
        
        # This month stats
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        context['emails_sent_month'] = EmailLog.objects.filter(
            sent_at__gte=month_start,
            status__in=['sent', 'delivered']
        ).count()
        
        context['campaigns_this_month'] = Campaign.objects.filter(
            created_at__gte=month_start
        ).count()
        
        context['new_contacts_month'] = Contact.objects.filter(
            created_at__gte=month_start
        ).count()
        
        # Recent activity
        context['recent_contacts'] = Contact.objects.select_related('company').order_by('-created_at')[:5]
        context['recent_deals'] = Deal.objects.select_related('contact').order_by('-created_at')[:5]
        context['recent_workflows'] = WorkflowExecution.objects.select_related('workflow', 'contact').order_by('-started_at')[:5]
        
        # Campaign stats
        campaigns = Campaign.objects.filter(status__in=['sent', 'sending']).values('name', 'sent_count', 'opened_count', 'clicked_count')
        context['campaign_stats'] = list(campaigns[:5])
        
        # Contact status breakdown
        context['contact_statuses'] = Contact.objects.values('status').annotate(
            count=Count('id')
        ) if hasattr(Contact, 'objects') else {}
        
        return context


# Import Count for aggregation
from django.db.models import Count
