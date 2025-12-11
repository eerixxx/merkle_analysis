"""
Django Admin configuration for BoostyFi models.
"""
from django.contrib import admin
from django.db.models import Sum, Count, F
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin

from .models import BoostyFiUser, BoostyFiPurchase, BoostyFiEarning


class BoostyFiPurchaseInline(admin.TabularInline):
    """Inline for user purchases."""
    model = BoostyFiPurchase
    extra = 0
    readonly_fields = ['original_id', 'amount', 'tx_hash', 'payment_status', 'created_at']
    fields = ['original_id', 'amount', 'payment_status', 'payment_type', 'created_at']
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False


class BoostyFiEarningInline(admin.TabularInline):
    """Inline for user earnings."""
    model = BoostyFiEarning
    fk_name = 'user'
    extra = 0
    readonly_fields = ['original_id', 'earning_type', 'amount', 'status', 'created_at']
    fields = ['original_id', 'earning_type', 'amount', 'status', 'referral_system_type', 'created_at']
    can_delete = False
    max_num = 15
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(BoostyFiUser)
class BoostyFiUserAdmin(MPTTModelAdmin):
    """Admin for BoostyFi users."""
    list_display = [
        'original_id', 'username', 'referral_type', 'short_wallet_display',
        'is_active', 'children_count', 'purchases_count', 'total_volume',
        'total_earnings', 'total_atla_display', 'created_at'
    ]
    list_filter = ['is_active', 'referral_type', 'is_superuser', 'is_staff', 'is_deleted', 'is_blocked']
    search_fields = ['username', 'wallet', 'evm_address', 'tron_address', 'email', 'referral_code', 'original_id']
    readonly_fields = [
        'original_id', 'original_lft', 'original_rght', 'original_tree_id',
        'original_level', 'created_at', 'updated_at'
    ]
    ordering = ['original_id']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('original_id', 'username', 'email')
        }),
        ('Wallet Addresses', {
            'fields': ('wallet', 'evm_address', 'tron_address')
        }),
        ('Referral Info', {
            'fields': ('referral_code', 'referral_code_confirmed', 'referral_type', 'parent')
        }),
        ('ATLA Balances', {
            'fields': ('locked_atla_balance', 'unlocked_atla_balance')
        }),
        ('Status', {
            'fields': ('is_active', 'is_superuser', 'is_staff', 'is_deleted', 'is_blocked')
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'parent_changed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Original Tree Data', {
            'fields': ('original_lft', 'original_rght', 'original_tree_id', 'original_level'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [BoostyFiPurchaseInline, BoostyFiEarningInline]
    
    def short_wallet_display(self, obj):
        return obj.short_wallet
    short_wallet_display.short_description = 'Wallet'
    
    def children_count(self, obj):
        return obj.get_children().count()
    children_count.short_description = 'Children'
    
    def purchases_count(self, obj):
        return obj.purchases.filter(payment_status='COMPLETED').count()
    purchases_count.short_description = 'Purchases'
    
    def total_volume(self, obj):
        result = obj.purchases.filter(
            payment_status='COMPLETED'
        ).aggregate(total=Sum('amount'))
        return f"${result['total'] or 0:.2f}"
    total_volume.short_description = 'Volume'
    
    def total_earnings(self, obj):
        result = obj.earnings.filter(
            status='WITHDRAWN'
        ).aggregate(total=Sum('amount'))
        return f"${result['total'] or 0:.2f}"
    total_earnings.short_description = 'Earnings'
    
    def total_atla_display(self, obj):
        return f"{obj.total_atla:.2f}"
    total_atla_display.short_description = 'ATLA'


@admin.register(BoostyFiPurchase)
class BoostyFiPurchaseAdmin(admin.ModelAdmin):
    """Admin for BoostyFi purchases."""
    list_display = [
        'original_id', 'buyer_display', 'amount', 'full_amount', 'discount_display',
        'payment_status', 'payment_type', 'short_tx_hash', 'created_at'
    ]
    list_filter = ['payment_status', 'payment_type', 'jggl_pack_id', 'referral_system_status']
    search_fields = ['tx_hash', 'buyer__username', 'buyer__wallet', 'original_id']
    readonly_fields = ['original_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 50
    raw_id_fields = ['buyer']
    
    def buyer_display(self, obj):
        if obj.buyer:
            return f"{obj.buyer.username or f'User {obj.buyer.original_id}'}"
        return f"ID: {obj.buyer_original_id}"
    buyer_display.short_description = 'Buyer'
    
    def discount_display(self, obj):
        if obj.discount_rate:
            return f"{float(obj.discount_rate) * 100:.1f}%"
        return "-"
    discount_display.short_description = 'Discount'
    
    def short_tx_hash(self, obj):
        if obj.tx_hash:
            return f"{obj.tx_hash[:10]}..."
        return "-"
    short_tx_hash.short_description = 'TX Hash'


@admin.register(BoostyFiEarning)
class BoostyFiEarningAdmin(admin.ModelAdmin):
    """Admin for BoostyFi earnings."""
    list_display = [
        'original_id', 'user_display', 'earning_type', 'amount',
        'status', 'referral_system_display', 'generation_level', 'created_at'
    ]
    list_filter = ['status', 'earning_type', 'referral_system_type', 'generation_level']
    search_fields = ['user__username', 'user__wallet', 'original_id', 'qualification_reason']
    readonly_fields = ['original_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 50
    raw_id_fields = ['user', 'buyer', 'purchase']
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username or f'User {obj.user.original_id}'}"
        return f"ID: {obj.user_original_id}"
    user_display.short_description = 'User'
    
    def referral_system_display(self, obj):
        return obj.referral_system_name
    referral_system_display.short_description = 'System'
