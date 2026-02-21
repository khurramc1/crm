from django.urls import path
from . import views

app_name = 'automations'

urlpatterns = [
    # Workflows
    path('', views.WorkflowListView.as_view(), name='workflow_list'),
    path('create/', views.WorkflowCreateView.as_view(), name='workflow_create'),
    path('<int:pk>/', views.WorkflowDetailView.as_view(), name='workflow_detail'),
    path('<int:pk>/edit/', views.WorkflowUpdateView.as_view(), name='workflow_update'),
    path('<int:pk>/delete/', views.WorkflowDeleteView.as_view(), name='workflow_delete'),
    path('<int:workflow_id>/step/create/', views.WorkflowStepCreateView.as_view(), name='step_create'),
    path('step/<int:pk>/edit/', views.WorkflowStepUpdateView.as_view(), name='step_update'),
    path('step/<int:pk>/delete/', views.WorkflowStepDeleteView.as_view(), name='step_delete'),
    
    # Executions
    path('executions/', views.WorkflowExecutionListView.as_view(), name='execution_list'),
]
