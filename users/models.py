from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """
    Extended user profile to store Google OAuth and Gmail information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    google_id = models.CharField(max_length=255, unique=True, blank=True)
    profile_picture = models.URLField(blank=True)
    
    # Gmail OAuth tokens (encrypted in production)
    gmail_access_token = models.TextField(blank=True)
    gmail_refresh_token = models.TextField(blank=True)
    gmail_token_expiry = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.email} - Profile"
