#!/usr/bin/env python3
"""
Скрипт для сброса пароля пользователя admin
"""
import os
import sys
import django

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

try:
    # Получаем пользователя admin
    user = User.objects.get(username='admin')
    
    # Устанавливаем новый пароль
    user.set_password('admin123')
    user.save()
    
    print(f"✓ Пароль успешно изменен для пользователя: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Суперпользователь: {user.is_superuser}")
    print(f"  Персонал: {user.is_staff}")
    print(f"\nНовые учетные данные:")
    print(f"  Username: admin")
    print(f"  Password: admin123")
    
except User.DoesNotExist:
    print("✗ Пользователь 'admin' не найден в базе данных")
    sys.exit(1)
except Exception as e:
    print(f"✗ Ошибка при изменении пароля: {e}")
    sys.exit(1)
