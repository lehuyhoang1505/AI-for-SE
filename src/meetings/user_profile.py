"""
User Profile Model for Email Verification
Extends Django's User model with email verification fields
"""
import secrets
import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings


class UserProfile(models.Model):
    """
    Extended user profile for email verification
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Email verification
    email_verified = models.BooleanField(default=False, verbose_name='Email đã xác thực')
    email_verification_token = models.CharField(
        max_length=64, 
        unique=True, 
        null=True, 
        blank=True,
        verbose_name='Token xác thực email'
    )
    token_created_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Thời gian tạo token'
    )
    
    # Password reset
    password_reset_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Token đặt lại mật khẩu'
    )
    password_reset_token_created_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian tạo token đặt lại mật khẩu'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile for {self.user.username}"
    
    def generate_verification_token(self):
        """Generate a new email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.token_created_at = timezone.now()
        self.save()
        return self.email_verification_token
    
    def is_verification_token_valid(self):
        """Check if the verification token is still valid (not expired)"""
        if not self.token_created_at:
            return False
        
        expiry_hours = getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS', 24)
        expiry_time = self.token_created_at + timedelta(hours=expiry_hours)
        return timezone.now() < expiry_time
    
    def verify_email(self):
        """Mark email as verified and clear the token"""
        self.email_verified = True
        self.email_verification_token = None
        self.token_created_at = None
        self.save()
    
    def generate_password_reset_token(self):
        """Generate a new password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_token_created_at = timezone.now()
        self.save()
        return self.password_reset_token
    
    def is_password_reset_token_valid(self):
        """Check if the password reset token is still valid (not expired)"""
        if not self.password_reset_token_created_at:
            return False
        
        expiry_hours = getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_HOURS', 1)
        expiry_time = self.password_reset_token_created_at + timedelta(hours=expiry_hours)
        return timezone.now() < expiry_time
    
    def clear_password_reset_token(self):
        """Clear password reset token after successful reset"""
        self.password_reset_token = None
        self.password_reset_token_created_at = None
        self.save()


# Signal to automatically create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
