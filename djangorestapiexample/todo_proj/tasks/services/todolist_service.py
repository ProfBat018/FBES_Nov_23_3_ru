from typing import Dict, Any
from django.db.models import QuerySet
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .base import BaseService
from ..models import TodoList, Task


class TodoListService(BaseService):
    """Сервис для работы со списками задач."""
    
    model = TodoList
    
    def get_user_queryset(self) -> QuerySet:
        """Списки текущего пользователя с аннотациями."""
        self.check_user_permission()
        return self.model.objects.filter(owner=self.user).annotate(
            tasks_count=Count('tasks'),
            open_tasks_count=Count('tasks', filter=Q(tasks__status__in=[
                Task.Status.TODO, Task.Status.IN_PROGRESS, Task.Status.BLOCKED
            ]))
        )
    
    def get_active_lists(self) -> QuerySet:
        """Активные (неархивированные) списки."""
        return self.get_user_queryset().filter(is_archived=False)
    
    def get_archived_lists(self) -> QuerySet:
        """Архивированные списки."""
        return self.get_user_queryset().filter(is_archived=True)
    
    def validate_create_permissions(self, data: Dict[str, Any]) -> None:
        """Проверка прав на создание списка."""
        self.check_user_permission()
        
        # Проверяем лимит списков пользователя
        user_lists_count = self.model.objects.filter(owner=self.user).count()
        if user_lists_count >= 50:  # Бизнес-правило: максимум 50 списков
            raise ValidationError("Превышен лимит списков задач (максимум 50)")
    
    def validate_update_permissions(self, instance: TodoList, data: Dict[str, Any]) -> None:
        """Проверка прав на обновление списка."""
        self.check_user_permission()
        
        if instance.owner != self.user:
            raise PermissionDenied("Нет прав на редактирование этого списка")
    
    def validate_delete_permissions(self, instance: TodoList) -> None:
        """Проверка прав на удаление списка."""
        self.check_user_permission()
        
        if instance.owner != self.user:
            raise PermissionDenied("Нет прав на удаление этого списка")
    
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при создании."""
        # Добавляем текущего пользователя как владельца
        data['owner'] = self.user
        
        # Проверяем обязательные поля
        if not data.get('title', '').strip():
            raise ValidationError("Название списка не может быть пустым")
        
        if len(data.get('title', '')) > 140:
            raise ValidationError("Название списка слишком длинное (максимум 140 символов)")
        
        # Проверяем уникальность названия для пользователя
        if self.model.objects.filter(
            owner=self.user, 
            title=data['title']
        ).exists():
            raise ValidationError("Список с таким названием уже существует")
        
        return data
    
    def validate_update_data(self, instance: TodoList, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при обновлении."""
        if 'title' in data:
            if not data['title'].strip():
                raise ValidationError("Название списка не может быть пустым")
            
            if len(data['title']) > 140:
                raise ValidationError("Название списка слишком длинное (максимум 140 символов)")
            
            # Проверяем уникальность названия (кроме текущего списка)
            if self.model.objects.filter(
                owner=self.user, 
                title=data['title']
            ).exclude(id=instance.id).exists():
                raise ValidationError("Список с таким названием уже существует")
        
        return data
    
    @transaction.atomic
    def archive_list(self, todo_list: TodoList) -> TodoList:
        """Архивировать список."""
        self.validate_update_permissions(todo_list, {})
        
        todo_list.is_archived = True
        todo_list.save(update_fields=['is_archived', 'updated_at'])
        
        return todo_list
    
    @transaction.atomic
    def unarchive_list(self, todo_list: TodoList) -> TodoList:
        """Разархивировать список."""
        self.validate_update_permissions(todo_list, {})
        
        todo_list.is_archived = False
        todo_list.save(update_fields=['is_archived', 'updated_at'])
        
        return todo_list
    
    @transaction.atomic
    def duplicate_list(self, todo_list: TodoList, new_title: str) -> TodoList:
        """Дублировать список со всеми задачами и тегами."""
        self.validate_update_permissions(todo_list, {})
        
        # Проверяем, что новое название уникально
        if self.model.objects.filter(owner=self.user, title=new_title).exists():
            raise ValidationError(f"Список с названием '{new_title}' уже существует")
        
        # Создаем новый список
        new_list = self.model.objects.create(
            owner=self.user,
            title=new_title,
            description=f"Копия: {todo_list.description}" if todo_list.description else "Копия списка"
        )
        
        # Копируем теги
        tag_mapping = {}  # Старый ID -> новый объект
        for old_tag in todo_list.tags.all():
            new_tag = new_list.tags.create(
                name=old_tag.name,
                color=old_tag.color
            )
            tag_mapping[old_tag.id] = new_tag
        
        # Копируем задачи
        for old_task in todo_list.tasks.all():
            new_task = new_list.tasks.create(
                title=old_task.title,
                description=old_task.description,
                priority=old_task.priority,
                due_date=old_task.due_date,
                status=Task.Status.TODO,  # Сбрасываем статус
                is_favorite=False,  # Сбрасываем избранное
                # assignee не копируем - оставляем пустым
            )
            
            # Копируем теги задачи
            old_task_tags = old_task.tags.all()
            new_tags = [tag_mapping[tag.id] for tag in old_task_tags if tag.id in tag_mapping]
            new_task.tags.set(new_tags)
        
        return new_list
    
    def get_list_statistics(self, todo_list: TodoList) -> Dict[str, Any]:
        """Получить статистику конкретного списка."""
        self.validate_update_permissions(todo_list, {})
        
        tasks = todo_list.tasks.all()
        
        stats = {
            'total_tasks': tasks.count(),
            'todo': tasks.filter(status=Task.Status.TODO).count(),
            'in_progress': tasks.filter(status=Task.Status.IN_PROGRESS).count(),
            'done': tasks.filter(status=Task.Status.DONE).count(),
            'blocked': tasks.filter(status=Task.Status.BLOCKED).count(),
            'high_priority': tasks.filter(priority__in=[
                Task.Priority.HIGH, Task.Priority.CRITICAL
            ]).count(),
            'with_due_date': tasks.filter(due_date__isnull=False).count(),
            'overdue': tasks.filter(
                due_date__lt=timezone.now(),
                status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]
            ).count() if tasks.exists() else 0,
        }
        
        return stats
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Получить общую статистику списков пользователя."""
        self.check_user_permission()
        
        lists = self.get_user_queryset()
        
        stats = {
            'total_lists': lists.count(),
            'active_lists': lists.filter(is_archived=False).count(),
            'archived_lists': lists.filter(is_archived=True).count(),
            'total_tasks': sum(lst.tasks_count for lst in lists),
            'total_open_tasks': sum(lst.open_tasks_count for lst in lists),
        }
        
        return stats
