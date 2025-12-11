"""
Serializers for Limitless API.
"""
from rest_framework import serializers
from django.db.models import Sum, Count, Q

from .models import LimitlessUser, LimitlessPurchase, LimitlessEarning


class LimitlessPurchaseSerializer(serializers.ModelSerializer):
    """Serializer for purchases."""
    
    class Meta:
        model = LimitlessPurchase
        fields = [
            'id', 'original_id', 'amount_usdt', 'tx_hash', 'payment_status',
            'pack_id', 'created_at'
        ]


class LimitlessEarningSerializer(serializers.ModelSerializer):
    """Serializer for earnings."""
    from_username = serializers.CharField(source='buyer.username', read_only=True)
    
    class Meta:
        model = LimitlessEarning
        fields = [
            'id', 'original_id', 'earning_type', 'level', 'percentage',
            'amount_usdt', 'status', 'from_username', 'created_at'
        ]


class LimitlessUserListSerializer(serializers.ModelSerializer):
    """Serializer for user list view."""
    children_count = serializers.SerializerMethodField()
    purchases_count = serializers.SerializerMethodField()
    direct_volume = serializers.SerializerMethodField()
    total_earnings = serializers.SerializerMethodField()
    
    class Meta:
        model = LimitlessUser
        fields = [
            'id', 'original_id', 'username', 'wallet', 'referral_code',
            'is_active', 'children_count', 'purchases_count',
            'direct_volume', 'total_earnings', 'created_at'
        ]
    
    def get_children_count(self, obj):
        return obj.get_children().count()
    
    def get_purchases_count(self, obj):
        return obj.purchases.filter(payment_status='COMPLETED').count()
    
    def get_direct_volume(self, obj):
        result = obj.purchases.filter(
            payment_status='COMPLETED'
        ).aggregate(total=Sum('amount_usdt'))
        return float(result['total'] or 0)
    
    def get_total_earnings(self, obj):
        result = obj.earnings.filter(
            status='WITHDRAWN'
        ).aggregate(total=Sum('amount_usdt'))
        return float(result['total'] or 0)


class LimitlessUserDetailSerializer(serializers.ModelSerializer):
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
    purchases = LimitlessPurchaseSerializer(many=True, read_only=True)
    recent_earnings = serializers.SerializerMethodField()
    earnings_by_type = serializers.SerializerMethodField()
    
    class Meta:
        model = LimitlessUser
        fields = [
            'id', 'original_id', 'username', 'email', 'wallet', 'referral_code',
            'referral_code_confirmed', 'is_active', 'is_superuser', 'is_staff',
            'date_joined', 'created_at', 'parent_username',
            'children_count', 'team_size', 'purchases_count', 'pending_purchases_count',
            'direct_volume', 'team_volume', 'total_earnings', 'pending_earnings',
            'purchases', 'recent_earnings', 'earnings_by_type'
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
        ).aggregate(total=Sum('amount_usdt'))
        return float(result['total'] or 0)
    
    def get_team_volume(self, obj):
        """Calculate total volume from user and all descendants."""
        descendants = obj.get_descendants(include_self=True)
        result = LimitlessPurchase.objects.filter(
            buyer__in=descendants,
            payment_status='COMPLETED'
        ).aggregate(total=Sum('amount_usdt'))
        return float(result['total'] or 0)
    
    def get_total_earnings(self, obj):
        result = obj.earnings.filter(
            status='WITHDRAWN'
        ).aggregate(total=Sum('amount_usdt'))
        return float(result['total'] or 0)
    
    def get_pending_earnings(self, obj):
        result = obj.earnings.filter(
            status='PENDING'
        ).aggregate(total=Sum('amount_usdt'))
        return float(result['total'] or 0)
    
    def get_recent_earnings(self, obj):
        earnings = obj.earnings.order_by('-created_at')[:15]
        return LimitlessEarningSerializer(earnings, many=True).data
    
    def get_earnings_by_type(self, obj):
        return list(obj.earnings.values('earning_type').annotate(
            count=Count('id'),
            total=Sum('amount_usdt')
        ))


class LimitlessUserTreeSerializer(serializers.ModelSerializer):
    """Serializer for tree node - optimized for performance."""
    children = serializers.SerializerMethodField()
    purchases_count = serializers.IntegerField(read_only=True, default=0)
    direct_volume = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True, default=0)
    total_earnings = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True, default=0)
    children_count = serializers.IntegerField(read_only=True, default=0)
    
    class Meta:
        model = LimitlessUser
        fields = [
            'id', 'original_id', 'username', 'wallet', 'is_active',
            'children_count', 'purchases_count', 'direct_volume',
            'total_earnings', 'children'
        ]
    
    def get_children(self, obj):
        max_depth = self.context.get('max_depth', 0)
        current_depth = self.context.get('current_depth', 0)
        
        if current_depth >= max_depth:
            return []
        
        # Use annotated children
        children = obj.get_children().annotate_tree_fields()
        return LimitlessUserTreeSerializer(
            children,
            many=True,
            context={
                'max_depth': max_depth,
                'current_depth': current_depth + 1
            }
        ).data


class LimitlessStatsSerializer(serializers.Serializer):
    """Serializer for overall statistics."""
    total_users = serializers.IntegerField()
    total_purchases = serializers.IntegerField()
    total_volume = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_earnings = serializers.DecimalField(max_digits=20, decimal_places=2)
    root_users = serializers.IntegerField()
