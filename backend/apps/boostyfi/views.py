"""
API Views for BoostyFi.
"""
from django.db.models import Sum, Count, F, Q, ExpressionWrapper, IntegerField
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import BoostyFiUser, BoostyFiPurchase, BoostyFiEarning
from .serializers import (
    BoostyFiUserListSerializer,
    BoostyFiUserDetailSerializer,
    BoostyFiUserTreeSerializer,
    BoostyFiPurchaseSerializer,
    BoostyFiEarningSerializer,
    BoostyFiStatsSerializer,
)


class BoostyFiUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for BoostyFi users.
    
    list: Get paginated list of users
    retrieve: Get user details
    tree: Get user's subtree
    roots: Get root users (no parent)
    """
    queryset = BoostyFiUser.objects.all()
    permission_classes = [AllowAny]  # Adjust as needed
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'referral_code_confirmed', 'referral_type']
    search_fields = ['username', 'wallet', 'evm_address', 'tron_address', 'referral_code', 'email']
    ordering_fields = ['created_at', 'username', 'original_id']
    ordering = ['original_id']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BoostyFiUserDetailSerializer
        if self.action in ['tree', 'roots']:
            return BoostyFiUserTreeSerializer
        return BoostyFiUserListSerializer
    
    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Get user's subtree with configurable depth."""
        user = self.get_object()
        max_depth = int(request.query_params.get('depth', 1))
        
        serializer = BoostyFiUserTreeSerializer(
            user,
            context={'max_depth': max_depth, 'current_depth': 0}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def roots(self, request):
        """Get root users (users without parents) with pagination, sorted by tree size descending."""
        # Annotate with tree_size using MPTT lft/rght: (rght - lft - 1) / 2 = number of descendants
        roots = self.queryset.filter(parent__isnull=True).annotate_tree_fields().annotate(
            tree_size=ExpressionWrapper(
                (F('rght') - F('lft') - 1) / 2,
                output_field=IntegerField()
            )
        ).order_by('-tree_size', 'original_id')  # Sort by tree size descending, then by original_id
        max_depth = int(request.query_params.get('depth', 0))  # Default 0 - no children
        
        # Pagination parameters
        limit = min(int(request.query_params.get('limit', 50)), 200)  # Max 200
        offset = int(request.query_params.get('offset', 0))
        
        total_count = roots.count()
        roots_page = roots[offset:offset + limit]
        
        serializer = BoostyFiUserTreeSerializer(
            roots_page,
            many=True,
            context={'max_depth': max_depth, 'current_depth': 0}
        )
        
        return Response({
            'results': serializer.data,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total_count,
        })
    
    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """Get user's ancestors (path from root to this user)."""
        user = self.get_object()
        ancestors = user.get_ancestors(include_self=True).annotate_tree_fields()
        
        serializer = BoostyFiUserTreeSerializer(
            ancestors,
            many=True,
            context={'max_depth': 0, 'current_depth': 0}
        )
        return Response({
            'user_id': user.id,
            'path': serializer.data,
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search users with autocomplete-friendly response."""
        query = request.query_params.get('q', '').strip()
        limit = min(int(request.query_params.get('limit', 20)), 50)
        
        if len(query) < 2:
            return Response({'results': [], 'query': query})
        
        users = self.queryset.filter(
            Q(username__icontains=query) |
            Q(wallet__icontains=query) |
            Q(referral_code__icontains=query) |
            Q(email__icontains=query) |
            Q(evm_address__icontains=query) |
            Q(tron_address__icontains=query)
        ).annotate_tree_fields()[:limit]
        
        serializer = BoostyFiUserTreeSerializer(
            users,
            many=True,
            context={'max_depth': 0, 'current_depth': 0}
        )
        return Response({
            'results': serializer.data,
            'query': query,
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get overall statistics."""
        total_users = BoostyFiUser.objects.count()
        
        completed_purchases = BoostyFiPurchase.objects.filter(
            payment_status='COMPLETED'
        )
        total_purchases = completed_purchases.count()
        total_volume = completed_purchases.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        withdrawn_earnings = BoostyFiEarning.objects.filter(
            status='WITHDRAWN'
        )
        total_earnings = withdrawn_earnings.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_atla = BoostyFiUser.objects.aggregate(
            total=Sum(F('locked_atla_balance') + F('unlocked_atla_balance'))
        )['total'] or 0
        
        root_users = BoostyFiUser.objects.filter(parent__isnull=True).count()
        
        data = {
            'total_users': total_users,
            'total_purchases': total_purchases,
            'total_volume': total_volume,
            'total_earnings': total_earnings,
            'total_atla': total_atla,
            'root_users': root_users,
        }
        
        serializer = BoostyFiStatsSerializer(data)
        return Response(serializer.data)


class BoostyFiPurchaseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for BoostyFi purchases."""
    queryset = BoostyFiPurchase.objects.all()
    serializer_class = BoostyFiPurchaseSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['payment_status', 'payment_type', 'jggl_pack_id', 'buyer_original_id']
    search_fields = ['tx_hash']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']


class BoostyFiEarningViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for BoostyFi earnings."""
    queryset = BoostyFiEarning.objects.all()
    serializer_class = BoostyFiEarningSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'earning_type', 'referral_system_type', 'user_original_id']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
