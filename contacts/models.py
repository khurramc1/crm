from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Company(models.Model):
    """Company/Organization model"""
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, blank=True, null=True, unique=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    size_choices = [
        ('1-10', '1-10'),
        ('11-50', '11-50'),
        ('51-200', '51-200'),
        ('201-500', '201-500'),
        ('501-1000', '501-1000'),
        ('1000+', '1000+'),
    ]
    size = models.CharField(max_length=20, choices=size_choices, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Contact(models.Model):
    """Contact/Lead model"""
    STATUS_CHOICES = [
        ('lead', 'Lead'),
        ('prospect', 'Prospect'),
        ('customer', 'Customer'),
        ('archived', 'Archived'),
    ]

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_contacts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Activity(models.Model):
    """Activity timeline for contacts"""
    ACTIVITY_TYPE_CHOICES = [
        ('note', 'Note'),
        ('email', 'Email'),
        ('call', 'Call'),
        ('meeting', 'Meeting'),
        ('task', 'Task'),
    ]

    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Activities"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.activity_type} - {self.contact.full_name}"
