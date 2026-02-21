from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
import csv
from io import TextIOWrapper

from .models import Contact, Company, Activity
from deals.models import Deal


class ContactListView(LoginRequiredMixin, ListView):
    """List all contacts with search and filter"""
    model = Contact
    template_name = 'contacts/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 20

    def get_queryset(self):
        queryset = Contact.objects.select_related('company', 'assigned_to')
        
        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by tags
        tags = self.request.GET.get('tags', '')
        if tags:
            queryset = queryset.filter(tags__icontains=tags)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Contact.STATUS_CHOICES
        return context


class ContactDetailView(LoginRequiredMixin, DetailView):
    """Contact detail view with activities and deals"""
    model = Contact
    template_name = 'contacts/contact_detail.html'
    context_object_name = 'contact'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.get_object()
        context['activities'] = contact.activities.all()
        context['deals'] = contact.deals.all()
        context['activity_types'] = Activity.ACTIVITY_TYPE_CHOICES
        return context


class ContactCreateView(LoginRequiredMixin, CreateView):
    """Create a new contact"""
    model = Contact
    template_name = 'contacts/contact_form.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'company', 'status', 'tags', 'notes']
    success_url = reverse_lazy('contacts:contact_list')

    def form_valid(self, form):
        form.instance.assigned_to = self.request.user
        return super().form_valid(form)


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    """Update contact details"""
    model = Contact
    template_name = 'contacts/contact_form.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'company', 'status', 'tags', 'notes', 'assigned_to']
    success_url = reverse_lazy('contacts:contact_list')


class ContactDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a contact"""
    model = Contact
    template_name = 'contacts/contact_confirm_delete.html'
    success_url = reverse_lazy('contacts:contact_list')


class ActivityCreateView(LoginRequiredMixin, CreateView):
    """Add an activity to a contact"""
    model = Activity
    template_name = 'contacts/activity_form.html'
    fields = ['activity_type', 'title', 'description']

    def dispatch(self, request, *args, **kwargs):
        self.contact = Contact.objects.get(id=kwargs['contact_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.contact = self.contact
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('contacts:contact_detail', kwargs={'pk': self.contact.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact'] = self.contact
        return context


class CompanyListView(LoginRequiredMixin, ListView):
    """List all companies"""
    model = Company
    template_name = 'contacts/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Count
        queryset = Company.objects.annotate(contact_count=Count('contacts'))
        
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(domain__icontains=search)
            )
        
        return queryset.order_by('-created_at')


class CompanyDetailView(LoginRequiredMixin, DetailView):
    """Company detail with associated contacts"""
    model = Company
    template_name = 'contacts/company_detail.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()
        context['contacts'] = company.contacts.all()
        context['deals'] = company.deals.all()
        return context


class CompanyCreateView(LoginRequiredMixin, CreateView):
    """Create a new company"""
    model = Company
    template_name = 'contacts/company_form.html'
    fields = ['name', 'domain', 'industry', 'size']
    success_url = reverse_lazy('contacts:company_list')


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    """Update company details"""
    model = Company
    template_name = 'contacts/company_form.html'
    fields = ['name', 'domain', 'industry', 'size']
    success_url = reverse_lazy('contacts:company_list')


class CompanyDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a company"""
    model = Company
    template_name = 'contacts/company_confirm_delete.html'
    success_url = reverse_lazy('contacts:company_list')


class ContactImportView(LoginRequiredMixin, CreateView):
    """Import contacts from CSV"""
    model = Contact
    template_name = 'contacts/contact_import.html'

    def post(self, request, *args, **kwargs):
        if 'csv_file' not in request.FILES:
            return redirect('contacts:contact_list')
        
        csv_file = request.FILES['csv_file']
        csv_content = TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(csv_content)
        
        imported_count = 0
        errors = []
        
        for row in reader:
            try:
                contact, created = Contact.objects.get_or_create(
                    email=row.get('email', ''),
                    defaults={
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'phone': row.get('phone', ''),
                        'status': row.get('status', 'lead'),
                        'tags': row.get('tags', ''),
                        'assigned_to': request.user,
                    }
                )
                if created:
                    imported_count += 1
            except Exception as e:
                errors.append(f"Row {reader.line_num}: {str(e)}")
        
        context = {
            'imported_count': imported_count,
            'errors': errors,
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(context)
        
        return render(request, 'contacts/contact_import.html', context)
