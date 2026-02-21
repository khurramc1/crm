from django.db import models
from django.contrib.auth.models import User
from contacts.models import Contact


class EmailTemplate(models.Model):
    """Email template with merge tags"""
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500)
    html_body = models.TextField()
    plain_body = models.TextField(blank=True)
    from_name = models.CharField(max_length=255, blank=True)
    from_email = models.EmailField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Campaign(models.Model):
    """Email campaign"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template = models.ForeignKey(EmailTemplate, on_delete=models.PROTECT)
    
    # Segment filter (JSON stored as CharField for simplicity)
    segment_filter = models.CharField(
        max_length=1000,
        blank=True,
        help_text="JSON filter: {\"status\": \"lead\", \"tags\": \"interested\"}"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    sent_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def open_rate(self):
        if self.sent_count == 0:
            return 0
        return (self.opened_count / self.sent_count) * 100

    @property
    def click_rate(self):
        if self.sent_count == 0:
            return 0
        return (self.clicked_count / self.sent_count) * 100


class EmailLog(models.Model):
    """Email send/open/click log"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]

    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='email_logs')
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Sent tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    email_id = models.CharField(max_length=255, blank=True, db_index=True)  # SendGrid ID
    
    # Open tracking
    opened_at = models.DateTimeField(null=True, blank=True)
    open_count = models.PositiveIntegerField(default=0)
    
    # Click tracking
    clicked_at = models.DateTimeField(null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)
    clicked_links = models.TextField(blank=True)  # JSON of clicked links
    
    # Error handling
    error_message = models.TextField(blank=True)
    
    # Merge tags rendering
    rendered_subject = models.CharField(max_length=500, blank=True)
    rendered_html = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('contact', 'campaign', 'template')

    def __str__(self):
        return f"{self.contact.email} - {self.status}"

