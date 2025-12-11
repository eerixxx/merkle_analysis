"""
Views for the users app.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import UserSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Get the current authenticated user's information.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
