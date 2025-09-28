# 🔐 JWT Аутентификация в Todo API

## ✅ Настройка завершена!

Swagger UI теперь полностью интегрирован с вашей JWT аутентификацией.

## 🚀 Быстрый старт

### 1. Запустите сервер

```bash
source .venv/bin/activate
python manage.py runserver
```

### 2. Откройте Swagger UI

http://127.0.0.1:8000/swagger/

### 3. Получите JWT токен

**Через Swagger UI:**

1. Найдите endpoint `POST /api/auth/token/`
2. Нажмите "Try it out"
3. Введите данные:
   ```json
   {
     "username": "testuser",
     "password": "testpass123"
   }
   ```
4. Нажмите "Execute"
5. Скопируйте `access` токен из ответа

### 4. Авторизируйтесь в Swagger

1. Нажмите кнопку **🔒 Authorize** в правом верхнем углу
2. В поле Value введите: `Bearer YOUR_ACCESS_TOKEN`
3. Нажмите "Authorize"
4. Нажмите "Close"

### 5. Тестируйте API

Теперь все защищенные endpoints доступны для тестирования!

## 📋 Доступные endpoints

### Аутентификация

- `POST /api/auth/token/` - получить токены
- `POST /api/auth/token/refresh/` - обновить access токен

### Основные ресурсы

- `GET /api/v1/tasks/` - список задач
- `POST /api/v1/tasks/` - создать задачу
- `GET /api/v1/todolists/` - списки задач
- `POST /api/v1/todolists/` - создать список
- И многие другие...

## ⚙️ Настройки токенов

- **Access токен**: действителен 1 час
- **Refresh токен**: действителен 7 дней
- **Алгоритм**: HS256
- **Заголовок**: `Authorization: Bearer <token>`

## 🔧 Тестовые данные

**Пользователь для тестирования:**

- Username: `testuser`
- Password: `testpass123`

## 💡 Полезные советы

1. **Автоматическое обновление токена**: Используйте refresh токен для получения нового access токена
2. **Тестирование через curl**:

   ```bash
   # Получить токен
   curl -X POST http://127.0.0.1:8000/api/auth/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "testpass123"}'

   # Использовать токен
   curl -X GET http://127.0.0.1:8000/api/v1/tasks/ \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

3. **Создание новых пользователей**: Запустите `python create_test_user.py` для создания дополнительных тестовых пользователей

## 🎯 Что изменилось в проекте

✅ Добавлены JWT endpoints  
✅ Настроена интеграция с Swagger  
✅ Обновлены настройки безопасности  
✅ Создан тестовый пользователь  
✅ Добавлена подробная документация

Ваш API готов к использованию! 🚀
