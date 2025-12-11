"""
Local development settings.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['*']

# Debug toolbar
INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405

INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Simplified password validation for development
AUTH_PASSWORD_VALIDATORS = []

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow all CORS origins in development
CORS_ALLOW_ALL_ORIGINS = True
