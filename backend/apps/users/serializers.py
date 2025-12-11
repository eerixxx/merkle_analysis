"""
Serializers for the users app.
"""
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'full_name',
            'is_seller',
            'is_staff',
            'is_active',
            'date_joined',
        )
        read_only_fields = ('id', 'username', 'is_staff', 'is_active', 'date_joined')
