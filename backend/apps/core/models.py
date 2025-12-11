"""
Base models for the project.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Platform(models.TextChoices):
    """Platform choices for seller assignments."""
    LIMITLESS = 'limitless', 'Limitless'
    BOOSTYFI = 'boostyfi', 'BoostyFi'


class SellerAssignment(TimeStampedModel):
    """
    Model to track which sellers have claimed which wallets.
    A wallet can be claimed by up to 5 sellers.
    """
    # The seller who claimed this wallet
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_assignments',
        limit_choices_to={'is_seller': True}
    )
    
    # Platform and wallet info
    platform = models.CharField(
        max_length=20,
        choices=Platform.choices,
        db_index=True
    )
    
    # The ID of the user (LimitlessUser or BoostyFiUser) being claimed
    target_user_id = models.IntegerField(db_index=True)
    
    # Cache the wallet address for display purposes
    wallet_address = models.CharField(max_length=255, blank=True)
    
    # Optional notes from the seller
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Seller Assignment'
        verbose_name_plural = 'Seller Assignments'
        ordering = ['-created_at']
        # Ensure unique seller-platform-user combination
        unique_together = [['seller', 'platform', 'target_user_id']]
        indexes = [
            models.Index(fields=['platform', 'target_user_id']),
        ]
    
    def __str__(self):
        return f"{self.seller.full_name or self.seller.username} -> {self.platform}:{self.target_user_id}"
    
    def clean(self):
        """Validate that no more than 5 sellers can claim the same wallet."""
        # Count existing assignments for this wallet
        existing_count = SellerAssignment.objects.filter(
            platform=self.platform,
            target_user_id=self.target_user_id
        ).exclude(pk=self.pk).count()
        
        if existing_count >= 5:
            raise ValidationError(
                f"This wallet already has {existing_count} sellers assigned. Maximum is 5."
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_assignments_for_user(cls, platform: str, target_user_id: int):
        """Get all seller assignments for a specific wallet."""
        return cls.objects.filter(
            platform=platform,
            target_user_id=target_user_id
        ).select_related('seller')
    
    @classmethod
    def get_seller_names_for_user(cls, platform: str, target_user_id: int) -> list:
        """Get list of seller names for a specific wallet."""
        assignments = cls.get_assignments_for_user(platform, target_user_id)
        return [
            {
                'id': a.id,
                'seller_id': a.seller.id,
                'seller_name': a.seller.full_name or a.seller.username,
                'seller_username': a.seller.username,
                'created_at': a.created_at.isoformat(),
            }
            for a in assignments
        ]
