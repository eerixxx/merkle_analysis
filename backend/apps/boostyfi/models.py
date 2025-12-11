"""
BoostyFi models for users, purchases, and earnings.
"""
from decimal import Decimal
from django.db import models
from django.db.models import Count, Sum, Q, OuterRef, Subquery, Value, DecimalField
from django.db.models.functions import Coalesce
from mptt.models import MPTTModel, TreeForeignKey
from mptt.managers import TreeManager

from apps.core.models import TimeStampedModel


class BoostyFiUserQuerySet(models.QuerySet):
    """Custom QuerySet with tree field annotations."""
    
    def annotate_tree_fields(self):
        """Add computed fields for tree display in a single query."""
        from .models import BoostyFiPurchase, BoostyFiEarning
        
        return self.annotate(
            children_count=Count('children', distinct=True),
            purchases_count=Count(
                'purchases',
                filter=Q(purchases__payment_status='COMPLETED'),
                distinct=True
            ),
            direct_volume=Coalesce(
                Sum('purchases__amount', filter=Q(purchases__payment_status='COMPLETED')),
                Value(Decimal('0'), output_field=DecimalField(max_digits=20, decimal_places=2))
            ),
            total_earnings=Coalesce(
                Sum('earnings__amount', filter=Q(earnings__status='WITHDRAWN')),
                Value(Decimal('0'), output_field=DecimalField(max_digits=20, decimal_places=2))
            )
        )


class BoostyFiUserManager(TreeManager):
    """Custom manager for BoostyFiUser."""
    
    def get_queryset(self):
        return BoostyFiUserQuerySet(self.model, using=self._db)
    
    def annotate_tree_fields(self):
        return self.get_queryset().annotate_tree_fields()


class ReferralType(models.TextChoices):
    INFLUENCER = 'Influencer', 'Influencer'
    KOL = 'KOL', 'KOL'
    DAISY = 'Daisy', 'Daisy'
    MLM = 'MLM', 'MLM'


class BoostyFiUser(MPTTModel, TimeStampedModel):
    """
    User model for BoostyFi hierarchy.
    Uses MPTT for efficient tree operations.
    """
    # Original ID from CSV
    original_id = models.IntegerField(unique=True, db_index=True)
    
    # User info
    username = models.CharField(max_length=255, blank=True, db_index=True)
    email = models.EmailField(blank=True, null=True)
    password_hash = models.CharField(max_length=255, blank=True)
    
    # Referral info
    referral_code = models.CharField(max_length=100, blank=True, db_index=True)
    referral_code_confirmed = models.BooleanField(default=False)
    referral_type = models.CharField(
        max_length=50,
        choices=ReferralType.choices,
        blank=True,
        db_index=True
    )
    
    # Wallet addresses
    wallet = models.CharField(max_length=255, blank=True, db_index=True)
    evm_address = models.CharField(max_length=255, blank=True)
    tron_address = models.CharField(max_length=255, blank=True)
    
    # ATLA balances
    locked_atla_balance = models.DecimalField(
        max_digits=30, decimal_places=18, default=0
    )
    unlocked_atla_balance = models.DecimalField(
        max_digits=30, decimal_places=18, default=0
    )
    
    # Hierarchy
    parent = TreeForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    
    # Status flags
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    
    # Timestamps from original data
    date_joined = models.DateTimeField(null=True, blank=True)
    parent_changed_at = models.DateTimeField(null=True, blank=True)
    
    # Original tree fields (for reference)
    original_lft = models.IntegerField(null=True, blank=True)
    original_rght = models.IntegerField(null=True, blank=True)
    original_tree_id = models.IntegerField(null=True, blank=True)
    original_level = models.IntegerField(null=True, blank=True)
    
    objects = BoostyFiUserManager()
    
    class MPTTMeta:
        order_insertion_by = ['username']
    
    class Meta:
        verbose_name = 'BoostyFi User'
        verbose_name_plural = 'BoostyFi Users'
        ordering = ['original_id']
    
    def __str__(self):
        return f"{self.username or f'User {self.original_id}'}"
    
    @property
    def short_wallet(self):
        wallet = self.wallet or self.evm_address or self.tron_address
        if wallet:
            return f"{wallet[:6]}...{wallet[-4:]}"
        return "No wallet"
    
    @property
    def total_atla(self):
        return self.locked_atla_balance + self.unlocked_atla_balance


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class PaymentType(models.TextChoices):
    CRYPTO = 'CRYPTO', 'Crypto'
    PAYID = 'PAYID', 'PayID'
    CARD = 'CARD', 'Card'


class BoostyFiPurchase(TimeStampedModel):
    """
    Purchase model for BoostyFi.
    """
    # Original ID from CSV
    original_id = models.IntegerField(unique=True, db_index=True)
    
    # Relationship
    buyer = models.ForeignKey(
        BoostyFiUser,
        on_delete=models.CASCADE,
        related_name='purchases',
        null=True,
        blank=True
    )
    buyer_original_id = models.IntegerField(null=True, blank=True, db_index=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    full_amount = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    
    tx_hash = models.CharField(max_length=255, blank=True, db_index=True)
    block_number = models.BigIntegerField(null=True, blank=True)
    contract_address = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Status
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.CRYPTO,
        db_index=True
    )
    referral_system_status = models.IntegerField(null=True, blank=True)
    
    # Pack info
    jggl_pack_id = models.IntegerField(null=True, blank=True)
    atla_pack_id = models.IntegerField(null=True, blank=True)
    
    # PayLink info
    paylink_invoice_id = models.CharField(max_length=255, blank=True)
    paylink_reference_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name = 'BoostyFi Purchase'
        verbose_name_plural = 'BoostyFi Purchases'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Purchase #{self.original_id} - ${self.amount}"


class EarningStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
    CANCELLED = 'CANCELLED', 'Cancelled'


class ReferralSystemType(models.IntegerChoices):
    INFLUENCER = 1, 'Influencer'
    KOL = 2, 'KOL'
    MLM = 3, 'MLM'


class EarningType(models.TextChoices):
    NETWORK = 'NETWORK', 'Network'


class BoostyFiEarning(TimeStampedModel):
    """
    Earning model for BoostyFi referral system.
    """
    # Original ID from CSV
    original_id = models.IntegerField(unique=True, db_index=True)
    
    # Relationships
    user = models.ForeignKey(
        BoostyFiUser,
        on_delete=models.CASCADE,
        related_name='earnings',
        null=True,
        blank=True
    )
    user_original_id = models.IntegerField(null=True, blank=True, db_index=True)
    
    buyer = models.ForeignKey(
        BoostyFiUser,
        on_delete=models.SET_NULL,
        related_name='earnings_generated',
        null=True,
        blank=True
    )
    buyer_original_id = models.IntegerField(null=True, blank=True, db_index=True)
    
    purchase = models.ForeignKey(
        BoostyFiPurchase,
        on_delete=models.SET_NULL,
        related_name='earnings',
        null=True,
        blank=True
    )
    purchase_original_id = models.IntegerField(null=True, blank=True, db_index=True)
    
    # Earning details
    earning_type = models.CharField(
        max_length=50,
        choices=EarningType.choices,
        default=EarningType.NETWORK,
        db_index=True
    )
    generation_level = models.IntegerField(null=True, blank=True)
    percentage = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    
    # Referral pool info
    referral_pool = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    referral_system_type = models.IntegerField(
        choices=ReferralSystemType.choices,
        null=True,
        blank=True,
        db_index=True
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=EarningStatus.choices,
        default=EarningStatus.PENDING,
        db_index=True
    )
    
    # MLM specific fields
    ppv = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    tv = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    tier = models.IntegerField(null=True, blank=True)
    qualification_reason = models.CharField(max_length=255, blank=True)
    tx_amount = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    rpr = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    calculated_at = models.DateTimeField(null=True, blank=True)
    
    # Sponsor earning
    is_sponsor_earning = models.BooleanField(default=False)
    sponsor_withhold_amount = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    
    class Meta:
        verbose_name = 'BoostyFi Earning'
        verbose_name_plural = 'BoostyFi Earnings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Earning #{self.original_id} - ${self.amount} ({self.earning_type})"
    
    @property
    def referral_system_name(self):
        mapping = {1: 'Influencer', 2: 'KOL', 3: 'MLM'}
        return mapping.get(self.referral_system_type, 'Unknown')
