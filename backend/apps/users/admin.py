from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'full_name', 'is_seller', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'is_seller')
    search_fields = ('username', 'email', 'full_name')
    ordering = ('-date_joined',)
    
    # Add custom fields to the admin form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('full_name', 'is_seller'),
        }),
    )
    
    # Add custom fields to the add user form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('full_name', 'is_seller'),
        }),
    )
