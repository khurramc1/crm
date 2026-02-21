from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    # Contacts
    path('', views.ContactListView.as_view(), name='contact_list'),
    path('create/', views.ContactCreateView.as_view(), name='contact_create'),
    path('<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_update'),
    path('<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),
    path('<int:contact_id>/activity/create/', views.ActivityCreateView.as_view(), name='activity_create'),
    
    # Companies
    path('companies/', views.CompanyListView.as_view(), name='company_list'),
    path('companies/create/', views.CompanyCreateView.as_view(), name='company_create'),
    path('companies/<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('companies/<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('companies/<int:pk>/delete/', views.CompanyDeleteView.as_view(), name='company_delete'),
    
    # Import
    path('import/', views.ContactImportView.as_view(), name='contact_import'),
]
