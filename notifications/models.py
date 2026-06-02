from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    """
    Notification model for user alerts.
    """
    NOTIFICATION_TYPES = [
        ('email_received', 'Email Received'),
        ('email_sent', 'Email Sent'),
        ('ai_error', 'AI Error'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    
    related_email = models.ForeignKey('emails.Email', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"

