"""
Serializers for BoostyFi API.
"""
from rest_framework import serializers
from django.db.models import Sum, Count

from .models import BoostyFiUser, BoostyFiPurchase, BoostyFiEarning


class BoostyFiPurchaseSerializer(serializers.ModelSerializer):
    """Serializer for purchases."""
    
    class Meta:
        model = BoostyFiPurchase
        fields = [
            'id', 'original_id', 'amount', 'full_amount', 'discount_rate',
            'tx_hash', 'payment_status', 'payment_type', 'jggl_pack_id',
            'created_at'
        ]


class BoostyFiEarningSerializer(serializers.ModelSerializer):
    """Serializer for earnings."""
    from_username = serializers.CharField(source='buyer.username', read_only=True)
    referral_system_name = serializers.ReadOnlyField()
    
    class Meta:
        model = BoostyFiEarning
        fields = [
            'id', 'original_id', 'earning_type', 'generation_level', 'percentage',
            'amount', 'status', 'referral_system_type', 'referral_system_name',
            'qualification_reason', 'from_username', 'created_at'
        ]


class BoostyFiUserListSerializer(serializers.ModelSerializer):
    """Serializer for user list view."""
    children_count = serializers.SerializerMethodField()
    purchases_count = serializers.SerializerMethodField()
    direct_volume = serializers.SerializerMethodField()
    total_earnings = serializers.SerializerMethodField()
    total_atla = serializers.ReadOnlyField()
    
    class Meta:
        model = BoostyFiUser
        fields = [
            'id', 'original_id', 'username', 'wallet', 'referral_code',
            'referral_type', 'is_active', 'children_count', 'purchases_count',
            'direct_volume', 'total_earnings', 'total_atla', 'created_at'
        ]
    
    def get_children_count(self, obj):
        return obj.get_children().count()
    
    def get_purchases_count(self, obj):
        return obj.purchases.filter(payment_status='COMPLETED').count()
    
    def get_direct_volume(self, obj):
        result = obj.purchases.filter(
            payment_status='COMPLETED'
        ).aggregate(total=Sum('amount'))
        return float(result['total'] or 0)
    
    def get_total_earnings(self, obj):
        result = obj.earnings.filter(
            status='WITHDRAWN'
        ).aggregate(total=Sum('amount'))
        return float(result['total'] or 0)


class BoostyFiUserDetailSerializer(serializers.ModelSerializer):
    """Serializer for user detail view."""
    children_count = serializers.SerializerMethodField()
    team_size = serializers.SerializerMethodField()
    purchases_count = serializers.SerializerMethodField()
    pending_purchases_count = serializers.SerializerMethodField()
    direct_volume = serializers.SerializerMethodField()
    team_volume = serializers.SerializerMethodField()
    total_earnings = serializers.SerializerMethodField()
    pending_earnings = serializers.SerializerMethodField()
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    purchases = BoostyFiPurchaseSerializer(many=True, read_only=True)
    recent_earnings = serializers.SerializerMethodField()
    earnings_by_type = serializers.SerializerMethodField()
    earnings_by_system = serializers.SerializerMethodField()
    total_atla = serializers.ReadOnlyField()
    
    class Meta:
        model = BoostyFiUser
        fields = [
            'id', 'original_id', 'username', 'email', 'wallet',
            'evm_address', 'tron_address', 'referral_code', 'referral_type',
            'referral_code_confirmed', 'is_active', 'is_superuser', 'is_staff',
            'locked_atla_balance', 'unlocked_atla_balance', 'total_atla',
            'date_joined', 'created_at', 'parent_username',
            'children_count', 'team_size', 'purchases_count', 'pending_purchases_count',
            'direct_volume', 'team_volume', 'total_earnings', 'pending_earnings',
            'purchases', 'recent_earnings', 'earnings_by_type', 'earnings_by_system'
        ]
    
    def get_children_count(self, obj):
        return obj.get_children().count()
    
    def get_team_size(self, obj):
        return obj.get_descendant_count()
    
    def get_purchases_count(self, obj):
        return obj.purchases.filter(payment_status='COMPLETED').count()
    
    def get_pending_purchases_count(self, obj):
        return obj.purchases.filter(payment_status='PENDING').count()
    
    def get_direct_volume(self, obj):
        result = obj.purchases.filter(
            payment_status='COMPLETED'
        ).aggregate(total=Sum('amount'))
        return float(result['total'] or 0)
    
    def get_team_volume(self, obj):
        """Calculate total volume from user and all descendants."""
        descendants = obj.get_descendants(include_self=True)
        result = BoostyFiPurchase.objects.filter(
            buyer__in=descendants,
            payment_status='COMPLETED'
        ).aggregate(total=Sum('amount'))
        return float(result['total'] or 0)
    
    def get_total_earnings(self, obj):
        result = obj.earnings.filter(
            status='WITHDRAWN'
        ).aggregate(total=Sum('amount'))
        return float(result['total'] or 0)
    
    def get_pending_earnings(self, obj):
        result = obj.earnings.filter(
            status='PENDING'
        ).aggregate(total=Sum('amount'))
        return float(result['total'] or 0)
    
    def get_recent_earnings(self, obj):
        earnings = obj.earnings.order_by('-created_at')[:15]
        return BoostyFiEarningSerializer(earnings, many=True).data
    
    def get_earnings_by_type(self, obj):
        return list(obj.earnings.values('earning_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        ))
    
    def get_earnings_by_system(self, obj):
        return list(obj.earnings.values('referral_system_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        ))


class BoostyFiUserTreeSerializer(serializers.ModelSerializer):
    """Serializer for tree node - optimized for performance."""
    children = serializers.SerializerMethodField()
    purchases_count = serializers.IntegerField(read_only=True, default=0)
    direct_volume = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True, default=0)
    total_earnings = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True, default=0)
    children_count = serializers.IntegerField(read_only=True, default=0)
    total_atla = serializers.ReadOnlyField()
    
    class Meta:
        model = BoostyFiUser
        fields = [
            'id', 'original_id', 'username', 'wallet', 'referral_type',
            'is_active', 'children_count', 'purchases_count', 'direct_volume',
            'total_earnings', 'total_atla', 'children'
        ]
    
    def get_children(self, obj):
        max_depth = self.context.get('max_depth', 0)
        current_depth = self.context.get('current_depth', 0)
        
        if current_depth >= max_depth:
            return []
        
        # Use annotated children if available, otherwise fetch
        children = obj.get_children().annotate_tree_fields()
        return BoostyFiUserTreeSerializer(
            children,
            many=True,
            context={
                'max_depth': max_depth,
                'current_depth': current_depth + 1
            }
        ).data


class BoostyFiStatsSerializer(serializers.Serializer):
    """Serializer for overall statistics."""
    total_users = serializers.IntegerField()
    total_purchases = serializers.IntegerField()
    total_volume = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_earnings = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_atla = serializers.DecimalField(max_digits=30, decimal_places=2)
    root_users = serializers.IntegerField()
