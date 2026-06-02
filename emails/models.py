from django.db import models
from django.contrib.auth.models import User

class Email(models.Model):
    """
    Email model to store email messages.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emails')
    gmail_message_id = models.CharField(max_length=255, blank=True)
    
    sender = models.EmailField()
    recipient = models.EmailField()
    cc = models.CharField(max_length=500, blank=True)
    bcc = models.CharField(max_length=500, blank=True)
    
    subject = models.CharField(max_length=500)
    body = models.TextField()
    html_body = models.TextField(blank=True)
    
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=True)
    is_starred = models.BooleanField(default=False)
    
    thread_id = models.CharField(max_length=255, blank=True)
    in_reply_to = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_sent']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.sender}"


class AILog(models.Model):
    """
    Log of all AI-generated content for auditing and improvement.
    """
    ACTION_CHOICES = [
        ('compose', 'Compose Email'),
        ('improve', 'Improve Email'),
        ('reply', 'Generate Reply'),
        ('subject', 'Generate Subject'),
        ('summarize', 'Summarize Email'),
    ]
    
    TONE_CHOICES = [
        ('formal', 'Formal'),
        ('friendly', 'Friendly'),
        ('concise', 'Concise'),
        ('assertive', 'Assertive'),
        ('professional', 'Professional'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default='professional')
    
    input_text = models.TextField()
    output_text = models.TextField()
    
    tokens_used = models.IntegerField(default=0)
    processing_time = models.FloatField(default=0.0)  # in seconds
    
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.action.upper()} - {self.user.email} - {self.created_at}"

