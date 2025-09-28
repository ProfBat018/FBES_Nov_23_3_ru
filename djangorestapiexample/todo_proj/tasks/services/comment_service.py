from typing import Dict, Any
from django.db.models import QuerySet
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from .base import BaseService
from ..models import Comment, Task


class CommentService(BaseService):
    """Сервис для работы с комментариями к задачам."""
    
    model = Comment
    
    def get_user_queryset(self) -> QuerySet:
        """Комментарии к задачам пользователя."""
        self.check_user_permission()
        return self.model.objects.filter(
            task__todo_list__owner=self.user
        ).select_related('task', 'author', 'task__todo_list')
    
    def get_task_comments(self, task: Task) -> QuerySet:
        """Комментарии к конкретной задаче."""
        self.check_user_permission()
        
        # Проверяем права доступа к задаче
        if task.todo_list.owner != self.user and task.assignee != self.user:
            raise PermissionDenied("Нет прав на просмотр комментариев к этой задаче")
        
        return self.model.objects.filter(task=task).select_related('author')
    
    def get_user_comments(self) -> QuerySet:
        """Комментарии, написанные текущим пользователем."""
        self.check_user_permission()
        return self.model.objects.filter(
            author=self.user
        ).select_related('task', 'task__todo_list')
    
    def validate_create_permissions(self, data: Dict[str, Any]) -> None:
        """Проверка прав на создание комментария."""
        self.check_user_permission()
        
        task = data.get('task')
        if task:
            # Можно комментировать только задачи из своих списков или назначенные на себя
            if task.todo_list.owner != self.user and task.assignee != self.user:
                raise PermissionDenied("Нет прав на комментирование этой задачи")
    
    def validate_update_permissions(self, instance: Comment, data: Dict[str, Any]) -> None:
        """Проверка прав на обновление комментария."""
        self.check_user_permission()
        
        # Редактировать можно только свои комментарии
        if instance.author != self.user:
            raise PermissionDenied("Нет прав на изменение этого комментария")
        
        # Дополнительно проверяем права на задачу
        task = instance.task
        if task.todo_list.owner != self.user and task.assignee != self.user:
            raise PermissionDenied("Нет прав на изменение комментариев к этой задаче")
    
    def validate_delete_permissions(self, instance: Comment) -> None:
        """Проверка прав на удаление комментария."""
        self.check_user_permission()
        
        # Удалять можно свои комментарии или если ты владелец задачи
        task = instance.task
        if (instance.author != self.user and 
            task.todo_list.owner != self.user):
            raise PermissionDenied("Нет прав на удаление этого комментария")
    
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при создании."""
        # Добавляем автора
        data['author'] = self.user
        
        # Проверяем обязательные поля
        if not data.get('text', '').strip():
            raise ValidationError("Текст комментария не может быть пустым")
        
        text = data['text'].strip()
        if len(text) > 2000:  # Разумное ограничение для комментария
            raise ValidationError("Комментарий слишком длинный (максимум 2000 символов)")
        
        data['text'] = text
        return data
    
    def validate_update_data(self, instance: Comment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при обновлении."""
        if 'text' in data:
            text = data['text'].strip()
            if not text:
                raise ValidationError("Текст комментария не может быть пустым")
            
            if len(text) > 2000:
                raise ValidationError("Комментарий слишком длинный (максимум 2000 символов)")
            
            data['text'] = text
        
        # Нельзя изменять автора и задачу
        data.pop('author', None)
        data.pop('task', None)
        
        return data
    
    @transaction.atomic
    def create_comment(self, task: Task, text: str) -> Comment:
        """Создать комментарий к задаче."""
        return self.create({
            'task': task,
            'text': text
        })
    
    def get_task_comments_count(self, task: Task) -> int:
        """Получить количество комментариев к задаче."""
        self.check_user_permission()
        
        if task.todo_list.owner != self.user and task.assignee != self.user:
            raise PermissionDenied("Нет прав на просмотр информации об этой задаче")
        
        return self.model.objects.filter(task=task).count()
    
    def get_recent_comments(self, limit: int = 10) -> QuerySet:
        """Получить последние комментарии пользователя."""
        return self.get_user_queryset().order_by('-created_at')[:limit]
    
    def search_comments(self, query: str) -> QuerySet:
        """Поиск по комментариям."""
        self.check_user_permission()
        
        if not query.strip():
            return self.model.objects.none()
        
        return self.get_user_queryset().filter(
            text__icontains=query.strip()
        ).order_by('-created_at')
    
    def get_comment_statistics(self) -> Dict[str, Any]:
        """Получить статистику комментариев пользователя."""
        self.check_user_permission()
        
        user_comments = self.get_user_comments()
        comments_to_user_tasks = self.get_user_queryset()
        
        stats = {
            'total_comments_written': user_comments.count(),
            'total_comments_received': comments_to_user_tasks.exclude(author=self.user).count(),
            'most_commented_task': None,
            'recent_activity': []
        }
        
        # Самая комментируемая задача
        from django.db.models import Count
        most_commented = (comments_to_user_tasks
                         .values('task__title', 'task__id')
                         .annotate(comment_count=Count('id'))
                         .order_by('-comment_count')
                         .first())
        
        if most_commented:
            stats['most_commented_task'] = {
                'task_id': most_commented['task__id'],
                'task_title': most_commented['task__title'],
                'comments_count': most_commented['comment_count']
            }
        
        # Последняя активность
        recent = self.get_recent_comments(5)
        for comment in recent:
            stats['recent_activity'].append({
                'id': comment.id,
                'task_title': comment.task.title,
                'text_preview': comment.text[:50] + '...' if len(comment.text) > 50 else comment.text,
                'created_at': comment.created_at,
                'is_own': comment.author == self.user
            })
        
        return stats
