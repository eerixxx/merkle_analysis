"""
URL configuration for Limitless API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LimitlessUserViewSet,
    LimitlessPurchaseViewSet,
    LimitlessEarningViewSet,
    WalletProfileViewSet,
)

app_name = 'limitless'

router = DefaultRouter()
router.register('users', LimitlessUserViewSet, basename='user')
router.register('purchases', LimitlessPurchaseViewSet, basename='purchase')
router.register('earnings', LimitlessEarningViewSet, basename='earning')
router.register('wallet-profiles', WalletProfileViewSet, basename='wallet-profile')

urlpatterns = [
    path('', include(router.urls)),
]
