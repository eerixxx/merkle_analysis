"""
URL configuration for BoostyFi API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    BoostyFiUserViewSet,
    BoostyFiPurchaseViewSet,
    BoostyFiEarningViewSet,
)

app_name = 'boostyfi'

router = DefaultRouter()
router.register('users', BoostyFiUserViewSet, basename='user')
router.register('purchases', BoostyFiPurchaseViewSet, basename='purchase')
router.register('earnings', BoostyFiEarningViewSet, basename='earning')

urlpatterns = [
    path('', include(router.urls)),
]
