from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q

from .models import Workflow, WorkflowStep, WorkflowExecution, WorkflowStepExecution
from .tasks import trigger_workflow
from emails.models import EmailTemplate
from contacts.models import Contact


class WorkflowListView(LoginRequiredMixin, ListView):
    """List all workflows"""
    model = Workflow
    template_name = 'automations/workflow_list.html'
    context_object_name = 'workflows'
    paginate_by = 20

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        queryset = Workflow.objects.select_related('created_by').prefetch_related('steps')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')


class WorkflowDetailView(LoginRequiredMixin, DetailView):
    """Workflow detail with steps"""
    model = Workflow
    template_name = 'automations/workflow_detail.html'
    context_object_name = 'workflow'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflow = self.get_object()
        context['steps'] = workflow.steps.all().order_by('order')
        context['executions'] = workflow.executions.all()[:10]
        return context


class WorkflowCreateView(LoginRequiredMixin, CreateView):
    """Create a new workflow"""
    model = Workflow
    template_name = 'automations/workflow_form.html'
    fields = ['name', 'description', 'trigger_event', 'trigger_data', 'is_active']
    success_url = reverse_lazy('automations:workflow_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trigger_choices'] = Workflow.TRIGGER_CHOICES
        return context


class WorkflowUpdateView(LoginRequiredMixin, UpdateView):
    """Update workflow"""
    model = Workflow
    template_name = 'automations/workflow_form.html'
    fields = ['name', 'description', 'trigger_event', 'trigger_data', 'is_active']
    success_url = reverse_lazy('automations:workflow_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trigger_choices'] = Workflow.TRIGGER_CHOICES
        return context


class WorkflowDeleteView(LoginRequiredMixin, DeleteView):
    """Delete workflow"""
    model = Workflow
    template_name = 'automations/workflow_confirm_delete.html'
    success_url = reverse_lazy('automations:workflow_list')


class WorkflowStepCreateView(LoginRequiredMixin, CreateView):
    """Create a new workflow step"""
    model = WorkflowStep
    template_name = 'automations/step_form.html'
    fields = ['order', 'action', 'delay_days', 'email_template', 'action_data', 'is_enabled']

    def dispatch(self, request, *args, **kwargs):
        self.workflow = Workflow.objects.get(id=kwargs['workflow_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.workflow = self.workflow
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('automations:workflow_detail', kwargs={'pk': self.workflow.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflow'] = self.workflow
        context['action_choices'] = WorkflowStep.ACTION_CHOICES
        context['templates'] = EmailTemplate.objects.all()
        return context


class WorkflowStepUpdateView(LoginRequiredMixin, UpdateView):
    """Update workflow step"""
    model = WorkflowStep
    template_name = 'automations/step_form.html'
    fields = ['order', 'action', 'delay_days', 'email_template', 'action_data', 'is_enabled']

    def get_success_url(self):
        return reverse_lazy('automations:workflow_detail', kwargs={'pk': self.object.workflow.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflow'] = self.object.workflow
        context['action_choices'] = WorkflowStep.ACTION_CHOICES
        context['templates'] = EmailTemplate.objects.all()
        return context


class WorkflowStepDeleteView(LoginRequiredMixin, DeleteView):
    """Delete workflow step"""
    model = WorkflowStep
    template_name = 'automations/step_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('automations:workflow_detail', kwargs={'pk': self.object.workflow.id})


class WorkflowExecutionListView(LoginRequiredMixin, ListView):
    """List workflow executions"""
    model = WorkflowExecution
    template_name = 'automations/execution_list.html'
    context_object_name = 'executions'
    paginate_by = 50

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        
        queryset = WorkflowExecution.objects.select_related('workflow', 'contact')
        
        if search:
            queryset = queryset.filter(
                Q(contact__first_name__icontains=search) |
                Q(contact__last_name__icontains=search) |
                Q(contact__email__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-started_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = WorkflowExecution.STATUS_CHOICES
        return context
