from django.db import models
from django.contrib.auth.models import User
from contacts.models import Contact
from emails.models import EmailTemplate


class Workflow(models.Model):
    """Automation workflow"""
    TRIGGER_CHOICES = [
        ('contact_created', 'Contact Created'),
        ('deal_stage_changed', 'Deal Stage Changed'),
        ('manual', 'Manual Trigger'),
        ('tag_added', 'Tag Added'),
        ('contact_updated', 'Contact Updated'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trigger_event = models.CharField(max_length=50, choices=TRIGGER_CHOICES)
    trigger_data = models.CharField(
        max_length=500,
        blank=True,
        help_text="JSON data for trigger (e.g., {\"tag\": \"sales\"}, {\"stage_id\": 1})"
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class WorkflowStep(models.Model):
    """Step in a workflow (email sends after X days)"""
    ACTION_CHOICES = [
        ('send_email', 'Send Email'),
        ('add_tag', 'Add Tag'),
        ('change_status', 'Change Contact Status'),
        ('assign_to', 'Assign to User'),
        ('wait', 'Wait/Delay'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')
    order = models.PositiveIntegerField(default=0)
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    delay_days = models.PositiveIntegerField(
        default=0,
        help_text="Days to wait before running this step"
    )
    
    # For send_email action
    email_template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_steps'
    )
    
    # For add_tag, status change, assign actions
    action_data = models.CharField(
        max_length=500,
        blank=True,
        help_text="JSON: {\"tag\": \"sale-ready\"} or {\"status\": \"prospect\"} or {\"user_id\": 1}"
    )
    
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ('workflow', 'order')

    def __str__(self):
        return f"{self.workflow.name} - Step {self.order}: {self.action}"


class WorkflowExecution(models.Model):
    """Track workflow executions for each contact"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='workflow_executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        unique_together = ('workflow', 'contact')

    def __str__(self):
        return f"{self.workflow.name} - {self.contact.full_name}"


class WorkflowStepExecution(models.Model):
    """Track individual step execution"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    workflow_execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name='step_executions'
    )
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    scheduled_for = models.DateTimeField()
    executed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['scheduled_for']

    def __str__(self):
        return f"{self.step} - {self.status}"

