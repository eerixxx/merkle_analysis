"""
Limitless models for users, purchases, and earnings.
"""
from decimal import Decimal
from django.db import models
from django.db.models import Count, Sum, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from mptt.models import MPTTModel, TreeForeignKey
from mptt.managers import TreeManager

from apps.core.models import TimeStampedModel


class LimitlessUserQuerySet(models.QuerySet):
    """Custom QuerySet with tree field annotations."""
    
    def annotate_tree_fields(self):
        """Add computed fields for tree display in a single query."""
        return self.annotate(
            children_count=Count('children', distinct=True),
            purchases_count=Count(
                'purchases',
                filter=Q(purchases__payment_status='COMPLETED'),
                distinct=True
            ),
            direct_volume=Coalesce(
                Sum('purchases__amount_usdt', filter=Q(purchases__payment_status='COMPLETED')),
                Value(Decimal('0'), output_field=DecimalField(max_digits=20, decimal_places=2))
            ),
            total_earnings=Coalesce(
                Sum('earnings__amount_usdt', filter=Q(earnings__status='WITHDRAWN')),
                Value(Decimal('0'), output_field=DecimalField(max_digits=20, decimal_places=2))
            )
        )


class LimitlessUserManager(TreeManager):
    """Custom manager for LimitlessUser."""
    
    def get_queryset(self):
        return LimitlessUserQuerySet(self.model, using=self._db)
    
    def annotate_tree_fields(self):
        return self.get_queryset().annotate_tree_fields()


class LimitlessUser(MPTTModel, TimeStampedModel):
    """
    User model for Limitless hierarchy.
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
    wallet = models.CharField(max_length=255, blank=True, db_index=True)
    
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
    
    objects = LimitlessUserManager()
    
    class MPTTMeta:
        order_insertion_by = ['username']
    
    class Meta:
        verbose_name = 'Limitless User'
        verbose_name_plural = 'Limitless Users'
        ordering = ['original_id']
    
    def __str__(self):
        return f"{self.username or f'User {self.original_id}'}"
    
    @property
    def short_wallet(self):
        if self.wallet:
            return f"{self.wallet[:6]}...{self.wallet[-4:]}"
        return "No wallet"


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class LimitlessPurchase(TimeStampedModel):
    """
    Purchase model for Limitless.
    """
    # Original ID from CSV
    original_id = models.IntegerField(unique=True, db_index=True)
    
    # Relationship
    buyer = models.ForeignKey(
        LimitlessUser,
        on_delete=models.CASCADE,
        related_name='purchases',
        null=True,
        blank=True
    )
    buyer_original_id = models.IntegerField(null=True, blank=True, db_index=True)
    
    # Payment details
    amount_usdt = models.DecimalField(max_digits=20, decimal_places=6, default=0)
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
    referral_system_status = models.IntegerField(null=True, blank=True)
    
    # Pack info
    pack_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Limitless Purchase'
        verbose_name_plural = 'Limitless Purchases'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Purchase #{self.original_id} - ${self.amount_usdt}"


class EarningStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
    CANCELLED = 'CANCELLED', 'Cancelled'


class EarningType(models.TextChoices):
    NETWORK = 'NETWORK', 'Network'
    BONUS_POOL = 'BONUS_POOL', 'Bonus Pool'
    LEGENDS_POOL = 'LEGENDS_POOL', 'Legends Pool'


class LimitlessEarning(TimeStampedModel):
    """
    Earning model for Limitless referral system.
    """
    # Original ID from CSV
    original_id = models.IntegerField(unique=True, db_index=True)
    
    # Relationships
    recipient = models.ForeignKey(
        LimitlessUser,
        on_delete=models.CASCADE,
        related_name='earnings',
        null=True,
        blank=True
    )
    recipient_original_id = models.IntegerField(null=True, blank=True, db_index=True)
    
    buyer = models.ForeignKey(
        LimitlessUser,
        on_delete=models.SET_NULL,
        related_name='earnings_generated',
        null=True,
        blank=True
    )
    buyer_original_id = models.IntegerField(null=True, blank=True, db_index=True)
    
    purchase = models.ForeignKey(
        LimitlessPurchase,
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
    level = models.IntegerField(null=True, blank=True)
    percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_usdt = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=EarningStatus.choices,
        default=EarningStatus.PENDING,
        db_index=True
    )
    
    # Additional flags
    is_grace_period = models.BooleanField(default=False)
    recipient_was_active = models.BooleanField(default=True)
    compression_applied = models.BooleanField(default=False)
    original_level = models.IntegerField(null=True, blank=True)
    
    # Distribution info
    shares_count = models.IntegerField(null=True, blank=True)
    distribution_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Limitless Earning'
        verbose_name_plural = 'Limitless Earnings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Earning #{self.original_id} - ${self.amount_usdt} ({self.earning_type})"
