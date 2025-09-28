#!/usr/bin/env python
"""
Скрипт для создания тестового пользователя для демо API.
Запускать после настройки проекта: python create_test_user.py
"""

import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_proj.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_user():
    username = 'testuser'
    email = 'test@example.com'
    password = 'testpass123'
    
    # Проверяем, существует ли пользователь
    if User.objects.filter(username=username).exists():
        print(f'Пользователь "{username}" уже существует!')
        user = User.objects.get(username=username)
    else:
        # Создаем нового пользователя
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        print(f'Создан тестовый пользователь "{username}"')
    
    print(f"""
=== ТЕСТОВЫЕ ДАННЫЕ ДЛЯ SWAGGER ===
Username: {username}
Password: {password}
Email: {email}

Используйте эти данные для получения JWT токена через:
POST /api/auth/token/

Пример запроса:
{{"username": "{username}", "password": "{password}"}}
""")
    
    return user

if __name__ == '__main__':
    create_test_user()
