"""
Admin configuration for core app.
"""
from django.contrib import admin
from .models import SellerAssignment


@admin.register(SellerAssignment)
class SellerAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'seller', 'seller_full_name', 'platform', 'target_user_id',
        'wallet_address_short', 'created_at'
    )
    list_filter = ('platform', 'created_at', 'seller')
    search_fields = ('seller__username', 'seller__full_name', 'wallet_address', 'target_user_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('seller',)
    
    fieldsets = (
        ('Assignment Info', {
            'fields': ('seller', 'platform', 'target_user_id', 'wallet_address')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def seller_full_name(self, obj):
        return obj.seller.full_name or obj.seller.username
    seller_full_name.short_description = 'Seller Name'
    
    def wallet_address_short(self, obj):
        if obj.wallet_address:
            return f"{obj.wallet_address[:6]}...{obj.wallet_address[-4:]}"
        return "N/A"
    wallet_address_short.short_description = 'Wallet'
