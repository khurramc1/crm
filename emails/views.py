from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q

from .models import EmailTemplate, Campaign, EmailLog
from .tasks import process_campaign, send_email_task
from contacts.models import Contact


class EmailTemplateListView(LoginRequiredMixin, ListView):
    """List all email templates"""
    model = EmailTemplate
    template_name = 'emails/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        queryset = EmailTemplate.objects.select_related('created_by')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(subject__icontains=search)
            )
        
        return queryset.order_by('-created_at')


class EmailTemplateDetailView(LoginRequiredMixin, DetailView):
    """View email template"""
    model = EmailTemplate
    template_name = 'emails/template_detail.html'
    context_object_name = 'template'


class EmailTemplateCreateView(LoginRequiredMixin, CreateView):
    """Create a new email template"""
    model = EmailTemplate
    template_name = 'emails/template_form.html'
    fields = ['name', 'subject', 'from_name', 'from_email', 'html_body', 'plain_body']
    success_url = reverse_lazy('emails:template_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['merge_tags'] = [
            '{{first_name}}', '{{last_name}}', '{{full_name}}',
            '{{email}}', '{{phone}}', '{{company_name}}'
        ]
        return context


class EmailTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Update email template"""
    model = EmailTemplate
    template_name = 'emails/template_form.html'
    fields = ['name', 'subject', 'from_name', 'from_email', 'html_body', 'plain_body']
    success_url = reverse_lazy('emails:template_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['merge_tags'] = [
            '{{first_name}}', '{{last_name}}', '{{full_name}}',
            '{{email}}', '{{phone}}', '{{company_name}}'
        ]
        return context


class EmailTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete email template"""
    model = EmailTemplate
    template_name = 'emails/template_confirm_delete.html'
    success_url = reverse_lazy('emails:template_list')


class CampaignListView(LoginRequiredMixin, ListView):
    """List all campaigns"""
    model = Campaign
    template_name = 'emails/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        
        queryset = Campaign.objects.select_related('template', 'created_by')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Campaign.STATUS_CHOICES
        return context


class CampaignDetailView(LoginRequiredMixin, DetailView):
    """Campaign detail with stats"""
    model = Campaign
    template_name = 'emails/campaign_detail.html'
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self.get_object()
        context['logs'] = campaign.logs.select_related('contact')
        context['sent_logs'] = campaign.logs.filter(status__in=['sent', 'delivered'])
        context['opened_logs'] = campaign.logs.filter(opened_at__isnull=False)
        context['clicked_logs'] = campaign.logs.filter(clicked_at__isnull=False)
        return context


class CampaignCreateView(LoginRequiredMixin, CreateView):
    """Create a new campaign"""
    model = Campaign
    template_name = 'emails/campaign_form.html'
    fields = ['name', 'description', 'template', 'segment_filter', 'status', 'scheduled_at']
    success_url = reverse_lazy('emails:campaign_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = EmailTemplate.objects.all()
        context['statuses'] = Campaign.STATUS_CHOICES
        return context


class CampaignUpdateView(LoginRequiredMixin, UpdateView):
    """Update campaign"""
    model = Campaign
    template_name = 'emails/campaign_form.html'
    fields = ['name', 'description', 'template', 'segment_filter', 'status', 'scheduled_at']
    success_url = reverse_lazy('emails:campaign_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = EmailTemplate.objects.all()
        context['statuses'] = Campaign.STATUS_CHOICES
        return context


class CampaignDeleteView(LoginRequiredMixin, DeleteView):
    """Delete campaign"""
    model = Campaign
    template_name = 'emails/campaign_confirm_delete.html'
    success_url = reverse_lazy('emails:campaign_list')


class CampaignSendView(LoginRequiredMixin, UpdateView):
    """Send campaign"""
    model = Campaign
    fields = ['status']

    def post(self, request, *args, **kwargs):
        campaign = self.get_object()
        
        if campaign.status not in ['draft', 'scheduled']:
            return JsonResponse({
                'success': False,
                'message': 'Campaign cannot be sent from current status'
            })
        
        # Queue the campaign for sending
        process_campaign.delay(campaign.id)
        
        campaign.status = 'scheduled'
        campaign.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Campaign queued for sending'
        })


class EmailLogListView(LoginRequiredMixin, ListView):
    """List email logs"""
    model = EmailLog
    template_name = 'emails/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        
        queryset = EmailLog.objects.select_related('contact', 'campaign', 'template')
        
        if search:
            queryset = queryset.filter(
                Q(contact__email__icontains=search) |
                Q(contact__first_name__icontains=search) |
                Q(contact__last_name__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = EmailLog.STATUS_CHOICES
        return context
