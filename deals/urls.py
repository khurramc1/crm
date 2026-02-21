from django.urls import path
from . import views

app_name = 'deals'

urlpatterns = [
    # Pipelines
    path('pipelines/', views.PipelineListView.as_view(), name='pipeline_list'),
    path('pipelines/create/', views.PipelineCreateView.as_view(), name='pipeline_create'),
    path('pipelines/<int:pk>/', views.PipelineDetailView.as_view(), name='pipeline_detail'),
    
    # Deals
    path('', views.DealListView.as_view(), name='deal_list'),
    path('kanban/', views.DealKanbanView.as_view(), name='deal_kanban'),
    path('create/', views.DealCreateView.as_view(), name='deal_create'),
    path('<int:pk>/', views.DealDetailView.as_view(), name='deal_detail'),
    path('<int:pk>/edit/', views.DealUpdateView.as_view(), name='deal_update'),
    path('<int:pk>/delete/', views.DealDeleteView.as_view(), name='deal_delete'),
    path('<int:pk>/move/', views.DealMoveView.as_view(), name='deal_move'),
]
