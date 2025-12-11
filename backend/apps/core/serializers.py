"""
Serializers for the core app.
"""
from rest_framework import serializers
from .models import SellerAssignment


class SellerInfoSerializer(serializers.Serializer):
    """Serializer for seller info in assignments."""
    id = serializers.IntegerField()
    seller_id = serializers.IntegerField()
    seller_name = serializers.CharField()
    seller_username = serializers.CharField()
    created_at = serializers.CharField()


class SellerAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for seller assignments."""
    seller_name = serializers.SerializerMethodField()
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    
    class Meta:
        model = SellerAssignment
        fields = [
            'id', 'seller', 'seller_name', 'seller_username',
            'platform', 'target_user_id', 'wallet_address',
            'notes', 'created_at'
        ]
        read_only_fields = ['seller', 'created_at']
    
    def get_seller_name(self, obj):
        return obj.seller.full_name or obj.seller.username


class ClaimWalletSerializer(serializers.Serializer):
    """Serializer for claiming a wallet."""
    platform = serializers.ChoiceField(choices=['limitless', 'boostyfi'])
    target_user_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate(self, data):
        """Validate that the target user exists and max 5 sellers."""
        platform = data['platform']
        target_user_id = data['target_user_id']
        
        # Verify target user exists
        if platform == 'limitless':
            from apps.limitless.models import LimitlessUser
            if not LimitlessUser.objects.filter(id=target_user_id).exists():
                raise serializers.ValidationError("Target user not found in Limitless")
        else:
            from apps.boostyfi.models import BoostyFiUser
            if not BoostyFiUser.objects.filter(id=target_user_id).exists():
                raise serializers.ValidationError("Target user not found in BoostyFi")
        
        # Check max 5 sellers
        existing_count = SellerAssignment.objects.filter(
            platform=platform,
            target_user_id=target_user_id
        ).count()
        
        if existing_count >= 5:
            raise serializers.ValidationError(
                f"This wallet already has {existing_count} sellers assigned. Maximum is 5."
            )
        
        return data
    
    def create(self, validated_data):
        """Create a seller assignment."""
        seller = self.context['request'].user
        platform = validated_data['platform']
        target_user_id = validated_data['target_user_id']
        
        # Get wallet address
        wallet_address = ''
        if platform == 'limitless':
            from apps.limitless.models import LimitlessUser
            user = LimitlessUser.objects.filter(id=target_user_id).first()
            if user:
                wallet_address = user.wallet or ''
        else:
            from apps.boostyfi.models import BoostyFiUser
            user = BoostyFiUser.objects.filter(id=target_user_id).first()
            if user:
                wallet_address = user.wallet or user.evm_address or user.tron_address or ''
        
        assignment, created = SellerAssignment.objects.get_or_create(
            seller=seller,
            platform=platform,
            target_user_id=target_user_id,
            defaults={
                'wallet_address': wallet_address,
                'notes': validated_data.get('notes', '')
            }
        )
        
        if not created:
            raise serializers.ValidationError("You have already claimed this wallet")
        
        return assignment


class UnclaimWalletSerializer(serializers.Serializer):
    """Serializer for unclaiming a wallet."""
    platform = serializers.ChoiceField(choices=['limitless', 'boostyfi'])
    target_user_id = serializers.IntegerField()
