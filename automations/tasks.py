import json
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone

from .models import Workflow, WorkflowExecution, WorkflowStep, WorkflowStepExecution
from contacts.models import Contact
from emails.models import EmailTemplate, EmailLog
from emails.tasks import send_email_task


@shared_task
def trigger_workflow(workflow_id, contact_id):
    """
    Trigger a workflow for a specific contact
    Creates workflow execution and schedules all steps
    """
    try:
        workflow = Workflow.objects.get(id=workflow_id, is_active=True)
        contact = Contact.objects.get(id=contact_id)
        
        # Get or create workflow execution
        execution, created = WorkflowExecution.objects.get_or_create(
            workflow=workflow,
            contact=contact,
            defaults={'status': 'pending'}
        )
        
        if not created and execution.status != 'pending':
            return f"Workflow already executed for {contact.full_name}"
        
        execution.status = 'in_progress'
        execution.save()
        
        # Get all steps in order
        steps = workflow.steps.filter(is_enabled=True).order_by('order')
        
        now = timezone.now()
        for step in steps:
            # Calculate when this step should run
            scheduled_for = now + timedelta(days=step.delay_days)
            
            step_execution = WorkflowStepExecution.objects.create(
                workflow_execution=execution,
                step=step,
                status='pending',
                scheduled_for=scheduled_for
            )
            
            # Queue the step execution task
            execute_workflow_step.apply_async(
                args=[step_execution.id],
                eta=scheduled_for
            )
        
        return f"Workflow {workflow.name} triggered for {contact.full_name}"
        
    except Workflow.DoesNotExist:
        raise
    except Contact.DoesNotExist:
        raise
    except Exception as e:
        raise


@shared_task
def execute_workflow_step(step_execution_id):
    """
    Execute a single workflow step
    """
    try:
        step_execution = WorkflowStepExecution.objects.get(id=step_execution_id)
        step = step_execution.step
        contact = step_execution.workflow_execution.contact
        
        action = step.action
        
        if action == 'send_email':
            # Send email via template
            if step.email_template:
                email_log = EmailLog.objects.create(
                    contact=contact,
                    template=step.email_template,
                    status='pending'
                )
                send_email_task.delay(email_log.id)
                step_execution.status = 'completed'
        
        elif action == 'add_tag':
            # Add tag to contact
            try:
                data = json.loads(step.action_data)
                tag = data.get('tag', '')
                if tag:
                    existing_tags = set(t.strip() for t in contact.tags.split(',') if t.strip())
                    existing_tags.add(tag)
                    contact.tags = ','.join(existing_tags)
                    contact.save()
                step_execution.status = 'completed'
            except (json.JSONDecodeError, KeyError):
                step_execution.status = 'failed'
                step_execution.error_message = 'Invalid action_data'
        
        elif action == 'change_status':
            # Change contact status
            try:
                data = json.loads(step.action_data)
                status = data.get('status', '')
                if status:
                    contact.status = status
                    contact.save()
                step_execution.status = 'completed'
            except (json.JSONDecodeError, KeyError):
                step_execution.status = 'failed'
                step_execution.error_message = 'Invalid action_data'
        
        elif action == 'assign_to':
            # Assign contact to user
            try:
                data = json.loads(step.action_data)
                user_id = data.get('user_id')
                if user_id:
                    from django.contrib.auth.models import User
                    user = User.objects.get(id=user_id)
                    contact.assigned_to = user
                    contact.save()
                step_execution.status = 'completed'
            except (json.JSONDecodeError, KeyError, Exception):
                step_execution.status = 'failed'
                step_execution.error_message = 'Invalid action_data or user not found'
        
        elif action == 'wait':
            # Just mark as completed (the delay is handled by eta)
            step_execution.status = 'completed'
        
        step_execution.executed_at = timezone.now()
        step_execution.save()
        
        # Check if all steps are completed
        all_completed = not step_execution.workflow_execution.step_executions.filter(
            status__in=['pending', 'in_progress']
        ).exists()
        
        if all_completed:
            step_execution.workflow_execution.status = 'completed'
            step_execution.workflow_execution.completed_at = timezone.now()
            step_execution.workflow_execution.save()
        
        return f"Step executed: {step.action}"
        
    except Exception as e:
        raise


@shared_task
def process_pending_workflows():
    """
    Process pending workflow steps that are due to run
    Runs every 5 minutes via Celery Beat
    """
    now = timezone.now()
    
    # Find pending step executions that are due
    pending_steps = WorkflowStepExecution.objects.filter(
        status='pending',
        scheduled_for__lte=now
    )
    
    for step in pending_steps:
        execute_workflow_step.delay(step.id)
    
    return f"Processed {pending_steps.count()} pending workflow steps"
