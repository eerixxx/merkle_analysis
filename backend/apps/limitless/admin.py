"""
Django Admin configuration for Limitless models.
"""
from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin

from .models import LimitlessUser, LimitlessPurchase, LimitlessEarning, WalletProfile


class LimitlessPurchaseInline(admin.TabularInline):
    """Inline for user purchases."""
    model = LimitlessPurchase
    extra = 0
    readonly_fields = ['original_id', 'amount_usdt', 'tx_hash', 'payment_status', 'created_at']
    fields = ['original_id', 'amount_usdt', 'payment_status', 'pack_id', 'created_at']
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False


class LimitlessEarningInline(admin.TabularInline):
    """Inline for user earnings."""
    model = LimitlessEarning
    fk_name = 'recipient'
    extra = 0
    readonly_fields = ['original_id', 'earning_type', 'amount_usdt', 'status', 'created_at']
    fields = ['original_id', 'earning_type', 'amount_usdt', 'status', 'level', 'created_at']
    can_delete = False
    max_num = 15
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(LimitlessUser)
class LimitlessUserAdmin(MPTTModelAdmin):
    """Admin for Limitless users."""
    list_display = [
        'original_id', 'username', 'short_wallet_display', 'referral_code',
        'is_active', 'children_count', 'purchases_count', 'total_volume',
        'total_earnings', 'created_at'
    ]
    list_filter = ['is_active', 'is_superuser', 'is_staff', 'is_deleted', 'is_blocked']
    search_fields = ['username', 'wallet', 'email', 'referral_code', 'original_id']
    readonly_fields = [
        'original_id', 'original_lft', 'original_rght', 'original_tree_id',
        'original_level', 'created_at', 'updated_at'
    ]
    ordering = ['original_id']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('original_id', 'username', 'email', 'wallet')
        }),
        ('Referral Info', {
            'fields': ('referral_code', 'referral_code_confirmed', 'parent')
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
    
    inlines = [LimitlessPurchaseInline, LimitlessEarningInline]
    
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
        ).aggregate(total=Sum('amount_usdt'))
        return f"${result['total'] or 0:.2f}"
    total_volume.short_description = 'Volume'
    
    def total_earnings(self, obj):
        result = obj.earnings.filter(
            status='WITHDRAWN'
        ).aggregate(total=Sum('amount_usdt'))
        return f"${result['total'] or 0:.2f}"
    total_earnings.short_description = 'Earnings'


@admin.register(LimitlessPurchase)
class LimitlessPurchaseAdmin(admin.ModelAdmin):
    """Admin for Limitless purchases."""
    list_display = [
        'original_id', 'buyer_display', 'amount_usdt', 'payment_status',
        'pack_id', 'short_tx_hash', 'created_at'
    ]
    list_filter = ['payment_status', 'pack_id', 'referral_system_status']
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
    
    def short_tx_hash(self, obj):
        if obj.tx_hash:
            return f"{obj.tx_hash[:10]}..."
        return "-"
    short_tx_hash.short_description = 'TX Hash'


@admin.register(LimitlessEarning)
class LimitlessEarningAdmin(admin.ModelAdmin):
    """Admin for Limitless earnings."""
    list_display = [
        'original_id', 'recipient_display', 'earning_type', 'amount_usdt',
        'status', 'level', 'percentage', 'created_at'
    ]
    list_filter = ['status', 'earning_type', 'level']
    search_fields = ['recipient__username', 'recipient__wallet', 'original_id']
    readonly_fields = ['original_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 50
    raw_id_fields = ['recipient', 'buyer', 'purchase']
    
    def recipient_display(self, obj):
        if obj.recipient:
            return f"{obj.recipient.username or f'User {obj.recipient.original_id}'}"
        return f"ID: {obj.recipient_original_id}"
    recipient_display.short_description = 'Recipient'


@admin.register(WalletProfile)
class WalletProfileAdmin(admin.ModelAdmin):
    """Admin for Wallet Profiles."""
    list_display = [
        'export_id', 'short_wallet_display', 'email', 'rank',
        'atla_balance', 'community_count', 'has_lp', 'has_chs', 'has_dsy',
        'email_verified', 'created_at'
    ]
    list_filter = [
        'rank', 'email_verified', 'is_seller', 'has_lp', 'has_chs', 'has_dsy',
        'need_private_zoom_call', 'want_business_dev_access', 'want_ceo_access',
        'can_communicate_english'
    ]
    search_fields = ['main_wallet', 'subwallets', 'email', 'telegram', 'rank']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-export_id']
    list_per_page = 50
    
    fieldsets = (
        ('Identification', {
            'fields': ('export_id', 'main_wallet', 'subwallets')
        }),
        ('Contact Info', {
            'fields': ('email', 'email_verified', 'is_seller', 'preferred_language', 'can_communicate_english')
        }),
        ('Balances & Rank', {
            'fields': ('atla_balance', 'rank', 'community_count')
        }),
        ('LP/CHS/DSY', {
            'fields': (('has_lp', 'lp_shares'), ('has_chs', 'ch_share'), ('has_dsy', 'dsy_bonus'))
        }),
        ('BoostyFi Tokens', {
            'fields': ('bfi_atla', 'bfi_jggl', 'jggl')
        }),
        ('Access Requests', {
            'fields': ('need_private_zoom_call', 'want_business_dev_access', 'want_ceo_access')
        }),
        ('Social/Contact', {
            'fields': ('telegram', 'facebook', 'whatsapp', 'viber', 'line', 'other_contact')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def short_wallet_display(self, obj):
        return obj.short_wallet
    short_wallet_display.short_description = 'Wallet'
