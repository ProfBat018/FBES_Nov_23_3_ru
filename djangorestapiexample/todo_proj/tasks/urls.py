from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import TaskViewSet, TodoListViewSet, TagViewSet, CommentViewSet

# Основной роутер для всех ViewSets
router = DefaultRouter()
router.register(r'todolists', TodoListViewSet, basename='todolist')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'comments', CommentViewSet, basename='comment')

# Вложенные роутеры для связанных ресурсов
todolists_router = nested_routers.NestedDefaultRouter(router, r'todolists', lookup='todolist')
todolists_router.register(r'tasks', TaskViewSet, basename='todolist-tasks')
todolists_router.register(r'tags', TagViewSet, basename='todolist-tags')

tasks_router = nested_routers.NestedDefaultRouter(router, r'tasks', lookup='task')
tasks_router.register(r'comments', CommentViewSet, basename='task-comments')

urlpatterns = [
    # Основные маршруты
    path('', include(router.urls)),
    # Вложенные маршруты
    path('', include(todolists_router.urls)),
    path('', include(tasks_router.urls)),
]

"""
Структура API endpoints:

ОСНОВНЫЕ РЕСУРСЫ:
GET    /api/v1/todolists/                    # Все списки пользователя
POST   /api/v1/todolists/                    # Создать список
GET    /api/v1/todolists/{id}/               # Конкретный список
PUT    /api/v1/todolists/{id}/               # Обновить список
DELETE /api/v1/todolists/{id}/               # Удалить список

GET    /api/v1/tasks/                        # Все задачи пользователя
POST   /api/v1/tasks/                        # Создать задачу
GET    /api/v1/tasks/{id}/                   # Конкретная задача
PUT    /api/v1/tasks/{id}/                   # Обновить задачу
DELETE /api/v1/tasks/{id}/                   # Удалить задачу

КАСТОМНЫЕ ACTIONS:
# TodoList actions
POST   /api/v1/todolists/{id}/archive/       # Архивировать список
POST   /api/v1/todolists/{id}/unarchive/     # Разархивировать список
GET    /api/v1/todolists/archived/           # Архивированные списки
GET    /api/v1/todolists/active/             # Активные списки
POST   /api/v1/todolists/{id}/duplicate/     # Дублировать список
GET    /api/v1/todolists/{id}/statistics/    # Статистика списка
GET    /api/v1/todolists/user_statistics/    # Общая статистика пользователя

# Task actions
POST   /api/v1/tasks/{id}/mark_done/         # Пометить выполненной (из сервиса!)
POST   /api/v1/tasks/{id}/mark_todo/         # Вернуть в работу
POST   /api/v1/tasks/{id}/mark_in_progress/  # Пометить в работе
POST   /api/v1/tasks/{id}/toggle_favorite/   # Переключить избранное
GET    /api/v1/tasks/my_tasks/               # Мои задачи (assignee)
GET    /api/v1/tasks/overdue/                # Просроченные
GET    /api/v1/tasks/high_priority/          # Высокий приоритет
GET    /api/v1/tasks/statistics/             # Статистика задач
POST   /api/v1/tasks/bulk_mark_done/         # Массовое завершение
POST   /api/v1/tasks/bulk_update_status/     # Массовое обновление статуса

# Tag actions
POST   /api/v1/tags/create_defaults/         # Создать теги по умолчанию
POST   /api/v1/tags/cleanup_unused/          # Удалить неиспользуемые теги
GET    /api/v1/tags/list_tags/               # Теги конкретного списка
GET    /api/v1/tags/usage_statistics/        # Статистика использования тегов

# Comment actions
GET    /api/v1/comments/task_comments/       # Комментарии к задаче
GET    /api/v1/comments/my_comments/         # Мои комментарии
GET    /api/v1/comments/recent/              # Последние комментарии
GET    /api/v1/comments/search/              # Поиск по комментариям
GET    /api/v1/comments/statistics/          # Статистика комментариев
POST   /api/v1/comments/add_to_task/         # Быстро добавить комментарий

ВЛОЖЕННЫЕ РЕСУРСЫ:
GET    /api/v1/todolists/{id}/tasks/         # Задачи конкретного списка
POST   /api/v1/todolists/{id}/tasks/         # Создать задачу в списке
GET    /api/v1/todolists/{id}/tags/          # Теги конкретного списка
POST   /api/v1/todolists/{id}/tags/          # Создать тег в списке
GET    /api/v1/tasks/{id}/comments/          # Комментарии к задаче
POST   /api/v1/tasks/{id}/comments/          # Добавить комментарий к задаче
"""
