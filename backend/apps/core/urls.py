"""
URL configuration for core API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SellerAssignmentViewSet

app_name = 'core'

router = DefaultRouter()
router.register('seller-assignments', SellerAssignmentViewSet, basename='seller-assignment')

urlpatterns = [
    path('', include(router.urls)),
]
