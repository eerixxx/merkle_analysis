"""
Custom User model for authentication.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for admin authentication.
    """
    email = models.EmailField(unique=True, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Convert empty email to None for unique constraint to work properly
        if self.email == '':
            self.email = None
        super().save(*args, **kwargs)
    full_name = models.CharField(max_length=255, blank=True, verbose_name='Full Name')
    is_seller = models.BooleanField(default=False, verbose_name='Seller')
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username
