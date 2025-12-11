"""
API Views for core functionality including seller assignments.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from .models import SellerAssignment
from .serializers import (
    SellerAssignmentSerializer,
    ClaimWalletSerializer,
    UnclaimWalletSerializer,
    SellerInfoSerializer,
)


class IsSeller(IsAuthenticated):
    """Permission class that checks if user is authenticated and is a seller."""
    
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return request.user.is_seller


class SellerAssignmentViewSet(viewsets.ViewSet):
    """
    ViewSet for seller assignment operations.
    """
    permission_classes = [IsSeller]
    
    @action(detail=False, methods=['post'])
    def claim(self, request):
        """Claim a wallet as a seller."""
        serializer = ClaimWalletSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assignment = serializer.save()
            return Response(
                SellerAssignmentSerializer(assignment).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def unclaim(self, request):
        """Remove yourself from a wallet."""
        serializer = UnclaimWalletSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        platform = serializer.validated_data['platform']
        target_user_id = serializer.validated_data['target_user_id']
        
        deleted, _ = SellerAssignment.objects.filter(
            seller=request.user,
            platform=platform,
            target_user_id=target_user_id
        ).delete()
        
        if deleted:
            return Response({'status': 'unclaimed'}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Assignment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        """Get all assignments for the current seller."""
        platform = request.query_params.get('platform')
        
        queryset = SellerAssignment.objects.filter(seller=request.user)
        if platform:
            queryset = queryset.filter(platform=platform)
        
        serializer = SellerAssignmentSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def for_user(self, request):
        """Get all seller assignments for a specific wallet (public endpoint)."""
        platform = request.query_params.get('platform')
        target_user_id = request.query_params.get('target_user_id')
        
        if not platform or not target_user_id:
            return Response(
                {'error': 'platform and target_user_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_user_id = int(target_user_id)
        except ValueError:
            return Response(
                {'error': 'target_user_id must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sellers = SellerAssignment.get_seller_names_for_user(platform, target_user_id)
        return Response({'sellers': sellers})
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def bulk_for_users(self, request):
        """
        Get seller assignments for multiple users at once.
        Query params: platform, user_ids (comma-separated)
        """
        platform = request.query_params.get('platform')
        user_ids_str = request.query_params.get('user_ids', '')
        
        if not platform:
            return Response(
                {'error': 'platform is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_ids = [int(x) for x in user_ids_str.split(',') if x.strip()]
        except ValueError:
            return Response(
                {'error': 'user_ids must be comma-separated integers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user_ids:
            return Response({'assignments': {}})
        
        # Limit to 200 users max
        user_ids = user_ids[:200]
        
        # Get all assignments for these users
        assignments = SellerAssignment.objects.filter(
            platform=platform,
            target_user_id__in=user_ids
        ).select_related('seller')
        
        # Group by target_user_id
        result = {}
        for assignment in assignments:
            if assignment.target_user_id not in result:
                result[assignment.target_user_id] = []
            result[assignment.target_user_id].append({
                'id': assignment.id,
                'seller_id': assignment.seller.id,
                'seller_name': assignment.seller.full_name or assignment.seller.username,
                'seller_username': assignment.seller.username,
                'created_at': assignment.created_at.isoformat(),
            })
        
        return Response({'assignments': result})
