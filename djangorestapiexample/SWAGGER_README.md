# Swagger API Документация

## Обзор

В проект добавлена поддержка Swagger для автоматической генерации API документации с помощью пакета `drf-yasg`.

## Доступные URL

После запуска сервера (`python manage.py runserver`) документация будет доступна по следующим адресам:

- **Swagger UI**: http://127.0.0.1:8000/swagger/
- **ReDoc**: http://127.0.0.1:8000/redoc/
- **JSON Schema**: http://127.0.0.1:8000/swagger.json
- **YAML Schema**: http://127.0.0.1:8000/swagger.yaml

## Настройки аутентификации

### Получение JWT токена:

1. **Через Swagger UI**: Используйте endpoint `POST /api/auth/token/` с username и password
2. **Через curl**:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/auth/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
   ```

### Использование токена в Swagger UI:

1. Получите access_token из ответа endpoint `/api/auth/token/`
2. Нажмите на кнопку "Authorize" в правом верхнем углу Swagger UI
3. В поле "Value" введите: `Bearer YOUR_ACCESS_TOKEN`
4. Нажмите "Authorize"

### Обновление токена:

- Access токен действителен 1 час
- Используйте endpoint `POST /api/auth/token/refresh/` с refresh_token для получения нового access_token

## Особенности

- Автоматически генерируется документация для всех ViewSets
- Поддержка JWT аутентификации
- Интерактивное тестирование API
- Детальные описания операций и параметров
- Схемы ответов с примерами

## API Endpoints

### Аутентификация

- `POST /api/auth/token/` - получить JWT токены (access + refresh)
- `POST /api/auth/token/refresh/` - обновить access токен

Основные группы endpoints:

### Задачи (Tasks)

- `GET /api/v1/tasks/` - список задач
- `POST /api/v1/tasks/` - создание задачи
- `GET /api/v1/tasks/{id}/` - получение задачи
- `PUT /api/v1/tasks/{id}/` - обновление задачи
- `DELETE /api/v1/tasks/{id}/` - удаление задачи

### Дополнительные действия для задач

- `POST /api/v1/tasks/{id}/mark_done/` - отметить как выполненную
- `POST /api/v1/tasks/{id}/toggle_favorite/` - добавить/убрать из избранного
- `GET /api/v1/tasks/statistics/` - статистика задач
- `GET /api/v1/tasks/my_tasks/` - мои задачи
- `GET /api/v1/tasks/overdue/` - просроченные задачи

### Списки задач (TodoLists)

- `GET /api/v1/todolists/` - список списков задач
- `POST /api/v1/todolists/` - создание списка
- И другие CRUD операции...

### Комментарии (Comments)

- Полный набор CRUD операций для комментариев к задачам

### Теги (Tags)

- Управление тегами для категоризации задач

## Установка

Swagger уже настроен и готов к использованию. Зависимости включены в `requirements.txt`.

### Установка зависимостей:

```bash
pip install -r requirements.txt
```

### Запуск сервера:

```bash
python manage.py runserver
```

## Исправленные проблемы

В процессе установки были исправлены следующие проблемы:

- Установлен пакет `drf-nested-routers` для поддержки nested роутеров
- Исправлены импорты `QuerySet` в сервисах (импорт из `django.db.models` вместо `typing`)
- Настроена поддержка JWT аутентификации в Swagger UI

## Состояние проекта

✅ Все зависимости установлены  
✅ Все импорты исправлены  
✅ Django проект проходит системные проверки  
✅ Swagger UI готов к использованию
