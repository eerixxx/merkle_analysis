"""
URL Configuration for the users app.
"""
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('me/', views.current_user, name='current_user'),
]
