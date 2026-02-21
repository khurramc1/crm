from django.urls import path
from . import views

app_name = 'emails'

urlpatterns = [
    # Email Templates
    path('templates/', views.EmailTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.EmailTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/', views.EmailTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<int:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/', views.EmailTemplateDeleteView.as_view(), name='template_delete'),
    
    # Campaigns
    path('campaigns/', views.CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/create/', views.CampaignCreateView.as_view(), name='campaign_create'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='campaign_detail'),
    path('campaigns/<int:pk>/edit/', views.CampaignUpdateView.as_view(), name='campaign_update'),
    path('campaigns/<int:pk>/delete/', views.CampaignDeleteView.as_view(), name='campaign_delete'),
    path('campaigns/<int:pk>/send/', views.CampaignSendView.as_view(), name='campaign_send'),
    
    # Email Logs
    path('logs/', views.EmailLogListView.as_view(), name='log_list'),
]
