"""
API Views for Limitless.
"""
from django.db.models import Sum, Count, Q, Case, When, Value, IntegerField, F, ExpressionWrapper
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import LimitlessUser, LimitlessPurchase, LimitlessEarning, WalletProfile
from .serializers import (
    LimitlessUserListSerializer,
    LimitlessUserDetailSerializer,
    LimitlessUserTreeSerializer,
    LimitlessPurchaseSerializer,
    LimitlessEarningSerializer,
    LimitlessStatsSerializer,
    WalletProfileSerializer,
    WalletProfileListSerializer,
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


class WalletProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for wallet profiles.
    
    list: Get paginated list of wallet profiles
    retrieve: Get wallet profile details by ID
    by_wallet: Get wallet profile by wallet address
    search: Search wallet profiles
    """
    queryset = WalletProfile.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rank', 'email_verified', 'is_seller', 'has_lp', 'has_chs', 'has_dsy']
    search_fields = ['main_wallet', 'subwallets', 'email', 'telegram', 'rank']
    ordering_fields = ['created_at', 'atla_balance', 'export_id', 'rank']
    ordering = ['-export_id']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WalletProfileListSerializer
        return WalletProfileSerializer
    
    @action(detail=False, methods=['get'], url_path='wallet/(?P<wallet_address>[^/.]+)')
    def by_wallet(self, request, wallet_address=None):
        """
        Get wallet profile by wallet address.
        Searches in main_wallet and subwallets.
        """
        if not wallet_address or len(wallet_address) < 10:
            return Response(
                {'error': 'Invalid wallet address'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search in main_wallet first
        profile = WalletProfile.objects.filter(main_wallet=wallet_address).first()
        
        # If not found, search in subwallets
        if not profile:
            profile = WalletProfile.objects.filter(
                subwallets__icontains=wallet_address
            ).first()
        
        if not profile:
            return Response(
                {'error': 'Wallet profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = WalletProfileSerializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search wallet profiles with autocomplete-friendly response."""
        query = request.query_params.get('q', '').strip()
        limit = min(int(request.query_params.get('limit', 20)), 50)
        
        if len(query) < 2:
            return Response({'results': [], 'query': query})
        
        profiles = self.queryset.filter(
            Q(main_wallet__icontains=query) |
            Q(subwallets__icontains=query) |
            Q(email__icontains=query) |
            Q(telegram__icontains=query) |
            Q(rank__icontains=query)
        )[:limit]
        
        serializer = WalletProfileListSerializer(profiles, many=True)
        return Response({
            'results': serializer.data,
            'query': query,
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get overall wallet profile statistics."""
        total_profiles = WalletProfile.objects.count()
        
        # Rank distribution
        rank_stats = list(
            WalletProfile.objects.values('rank')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Totals
        totals = WalletProfile.objects.aggregate(
            total_atla=Sum('atla_balance'),
            total_jggl=Sum('jggl'),
            total_bfi_atla=Sum('bfi_atla'),
            total_bfi_jggl=Sum('bfi_jggl'),
            total_community=Sum('community_count'),
        )
        
        # Feature counts
        feature_counts = {
            'has_lp': WalletProfile.objects.filter(has_lp=True).count(),
            'has_chs': WalletProfile.objects.filter(has_chs=True).count(),
            'has_dsy': WalletProfile.objects.filter(has_dsy=True).count(),
            'email_verified': WalletProfile.objects.filter(email_verified=True).count(),
            'is_seller': WalletProfile.objects.filter(is_seller=True).count(),
            'need_private_zoom_call': WalletProfile.objects.filter(need_private_zoom_call=True).count(),
            'want_business_dev_access': WalletProfile.objects.filter(want_business_dev_access=True).count(),
            'want_ceo_access': WalletProfile.objects.filter(want_ceo_access=True).count(),
        }
        
        return Response({
            'total_profiles': total_profiles,
            'rank_distribution': rank_stats,
            'totals': totals,
            'feature_counts': feature_counts,
        })
