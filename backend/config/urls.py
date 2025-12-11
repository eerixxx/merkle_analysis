"""
URL Configuration for the project.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Prometheus metrics
    path('', include('django_prometheus.urls')),
    
    # JWT Authentication
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('api/v1/users/', include('apps.users.urls', namespace='users')),
    path('api/v1/core/', include('apps.core.urls', namespace='core')),
    path('api/v1/limitless/', include('apps.limitless.urls', namespace='limitless')),
    path('api/v1/boostyfi/', include('apps.boostyfi.urls', namespace='boostyfi')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
