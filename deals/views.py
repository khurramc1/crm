from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q

from .models import Pipeline, Stage, Deal
from contacts.models import Contact
from automations.tasks import trigger_workflow


class PipelineListView(LoginRequiredMixin, ListView):
    """List all pipelines"""
    model = Pipeline
    template_name = 'deals/pipeline_list.html'
    context_object_name = 'pipelines'

    def get_queryset(self):
        return Pipeline.objects.prefetch_related('stages').order_by('-created_at')


class PipelineDetailView(LoginRequiredMixin, DetailView):
    """Pipeline detail with stages"""
    model = Pipeline
    template_name = 'deals/pipeline_detail.html'
    context_object_name = 'pipeline'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pipeline = self.get_object()
        context['stages'] = pipeline.stages.all()
        return context


class PipelineCreateView(LoginRequiredMixin, CreateView):
    """Create a new pipeline"""
    model = Pipeline
    template_name = 'deals/pipeline_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('deals:pipeline_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class DealListView(LoginRequiredMixin, ListView):
    """List all deals with search and filter"""
    model = Deal
    template_name = 'deals/deal_list.html'
    context_object_name = 'deals'
    paginate_by = 20

    def get_queryset(self):
        queryset = Deal.objects.select_related('contact', 'company', 'pipeline', 'stage', 'assigned_to')
        
        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(contact__first_name__icontains=search) |
                Q(contact__last_name__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by pipeline
        pipeline_id = self.request.GET.get('pipeline', '')
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Deal.STATUS_CHOICES
        context['pipelines'] = Pipeline.objects.all()
        context['total_value'] = sum(d.value for d in self.get_queryset())
        return context


class DealKanbanView(LoginRequiredMixin, TemplateView):
    """Kanban board view for deals"""
    template_name = 'deals/deal_kanban.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        pipeline_id = self.kwargs.get('pipeline_id')
        if pipeline_id:
            pipeline = get_object_or_404(Pipeline, id=pipeline_id)
        else:
            pipeline = Pipeline.objects.first()
        
        context['pipeline'] = pipeline
        context['stages'] = pipeline.stages.prefetch_related(
            'deal_set'
        ).order_by('order') if pipeline else []
        
        return context


class DealDetailView(LoginRequiredMixin, DetailView):
    """Deal detail view"""
    model = Deal
    template_name = 'deals/deal_detail.html'
    context_object_name = 'deal'


class DealCreateView(LoginRequiredMixin, CreateView):
    """Create a new deal"""
    model = Deal
    template_name = 'deals/deal_form.html'
    fields = ['title', 'description', 'value', 'currency', 'contact', 'company', 'pipeline', 'stage', 'close_date']
    success_url = reverse_lazy('deals:deal_list')

    def form_valid(self, form):
        form.instance.assigned_to = self.request.user
        form.instance.status = 'open'
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contacts'] = Contact.objects.all()
        context['pipelines'] = Pipeline.objects.all()
        return context


class DealUpdateView(LoginRequiredMixin, UpdateView):
    """Update deal details"""
    model = Deal
    template_name = 'deals/deal_form.html'
    fields = ['title', 'description', 'value', 'currency', 'contact', 'company', 'pipeline', 'stage', 'status', 'close_date', 'assigned_to']
    success_url = reverse_lazy('deals:deal_list')


class DealDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a deal"""
    model = Deal
    template_name = 'deals/deal_confirm_delete.html'
    success_url = reverse_lazy('deals:deal_list')


class DealMoveView(LoginRequiredMixin, UpdateView):
    """Move deal to a different stage (via AJAX)"""
    model = Deal
    fields = ['stage']

    def post(self, request, *args, **kwargs):
        deal = self.get_object()
        new_stage_id = request.POST.get('stage_id')
        
        if new_stage_id:
            try:
                new_stage = Stage.objects.get(id=new_stage_id)
                deal.stage = new_stage
                deal.save()
                
                # Trigger workflow if deal stage changed
                from automations.models import Workflow
                workflows = Workflow.objects.filter(
                    trigger_event='deal_stage_changed',
                    is_active=True
                )
                for workflow in workflows:
                    trigger_workflow.delay(workflow.id, deal.contact.id)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Deal moved successfully'
                })
            except Stage.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Stage not found'
                })
        
        return JsonResponse({
            'success': False,
            'message': 'No stage provided'
        })
