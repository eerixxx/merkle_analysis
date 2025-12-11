"""
API Views for Limitless.
"""
from django.db.models import Sum, Count, Q, Case, When, Value, IntegerField
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import LimitlessUser, LimitlessPurchase, LimitlessEarning
from .serializers import (
    LimitlessUserListSerializer,
    LimitlessUserDetailSerializer,
    LimitlessUserTreeSerializer,
    LimitlessPurchaseSerializer,
    LimitlessEarningSerializer,
    LimitlessStatsSerializer,
)


class LimitlessUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Limitless users.
    
    list: Get paginated list of users
    retrieve: Get user details
    tree: Get user's subtree
    roots: Get root users (no parent)
    """
    queryset = LimitlessUser.objects.all()
    permission_classes = [AllowAny]  # Adjust as needed
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'referral_code_confirmed']
    search_fields = ['username', 'wallet', 'referral_code', 'email']
    ordering_fields = ['created_at', 'username', 'original_id']
    ordering = ['original_id']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LimitlessUserDetailSerializer
        if self.action in ['tree', 'roots']:
            return LimitlessUserTreeSerializer
        return LimitlessUserListSerializer
    
    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Get user's subtree with configurable depth."""
        user = self.get_object()
        max_depth = int(request.query_params.get('depth', 2))
        
        serializer = LimitlessUserTreeSerializer(
            user,
            context={'max_depth': max_depth, 'current_depth': 0}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def roots(self, request):
        """Get root users (users without parents) with pagination."""
        roots = self.queryset.filter(parent__isnull=True).annotate_tree_fields().order_by('original_id')
        max_depth = int(request.query_params.get('depth', 0))  # Default 0 - no children
        
        # Pagination parameters
        limit = min(int(request.query_params.get('limit', 50)), 200)  # Max 200
        offset = int(request.query_params.get('offset', 0))
        
        total_count = roots.count()
        roots_page = roots[offset:offset + limit]
        
        serializer = LimitlessUserTreeSerializer(
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
        
        serializer = LimitlessUserTreeSerializer(
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
            Q(email__icontains=query)
        ).annotate_tree_fields()[:limit]
        
        serializer = LimitlessUserTreeSerializer(
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
        total_users = LimitlessUser.objects.count()
        
        completed_purchases = LimitlessPurchase.objects.filter(
            payment_status='COMPLETED'
        )
        total_purchases = completed_purchases.count()
        total_volume = completed_purchases.aggregate(
            total=Sum('amount_usdt')
        )['total'] or 0
        
        withdrawn_earnings = LimitlessEarning.objects.filter(
            status='WITHDRAWN'
        )
        total_earnings = withdrawn_earnings.aggregate(
            total=Sum('amount_usdt')
        )['total'] or 0
        
        root_users = LimitlessUser.objects.filter(parent__isnull=True).count()
        
        data = {
            'total_users': total_users,
            'total_purchases': total_purchases,
            'total_volume': total_volume,
            'total_earnings': total_earnings,
            'root_users': root_users,
        }
        
        serializer = LimitlessStatsSerializer(data)
        return Response(serializer.data)


class LimitlessPurchaseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Limitless purchases."""
    queryset = LimitlessPurchase.objects.all()
    serializer_class = LimitlessPurchaseSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['payment_status', 'pack_id', 'buyer_original_id']
    search_fields = ['tx_hash']
    ordering_fields = ['created_at', 'amount_usdt']
    ordering = ['-created_at']


class LimitlessEarningViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Limitless earnings."""
    queryset = LimitlessEarning.objects.all()
    serializer_class = LimitlessEarningSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'earning_type', 'recipient_original_id']
    ordering_fields = ['created_at', 'amount_usdt']
    ordering = ['-created_at']
