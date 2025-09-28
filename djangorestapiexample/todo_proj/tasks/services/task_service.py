from typing import Dict, Any, List, Optional
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .base import BaseService
from ..models import Task, TodoList, Tag


"""
Обычный сервис, который добавляет бизнес-логику к модели Task
Если сравнивать с логикой из ASP.NET Core, то этот сервис - это Service Layer.
"""
class TaskService(BaseService): # Все сервисы наследуются от BaseService 
    """Сервис для работы с задачами - вся бизнес-логика здесь."""
    
    # Модель, который требует BaseService 
    model = Task 
    
    def get_user_queryset(self) -> QuerySet:
        """Задачи пользователя (из его списков)."""
        self.check_user_permission()

        """
        1. self - это this 
        2. self.user - это текущий пользователь
        3. обращение в БД происходит через саму модель
        4. select_related - это метод, который позволяет загрузить связанные объекты вместе с основным объектом
        Если говрить на языке C#, то это метод Include в EF Core. В данном случае 
        мы посылаем туда два параметра: todo_list и assignee. 
        5. prefetch_related загружает связанные объекты вместе с основным объектом, но 
        связанные данные загружаются до основного объекта.
        6. В конце мы возвращаем queryset, который содержит все задачи пользователя.
        """
        return self.model.objects.filter(
            todo_list__owner=self.user
        ).select_related('todo_list', 'assignee').prefetch_related('tags')
    
    def get_assigned_tasks(self) -> QuerySet:
        """Задачи, назначенные на текущего пользователя."""
        self.check_user_permission()
        return self.model.objects.filter(
            assignee=self.user
        ).select_related('todo_list', 'assignee').prefetch_related('tags')
    
    def get_overdue_tasks(self) -> QuerySet:
        """Просроченные задачи пользователя."""
        self.check_user_permission()
        return self.get_user_queryset().filter(
            due_date__lt=timezone.now(),
            status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]
        )
    
    def get_high_priority_tasks(self) -> QuerySet:
        """Задачи с высоким приоритетом."""
        self.check_user_permission()
        return self.get_user_queryset().filter(
            priority__in=[Task.Priority.HIGH, Task.Priority.CRITICAL],
            status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]
        )
    
    def validate_create_permissions(self, data: Dict[str, Any]) -> None:
        """Проверка прав на создание задачи."""
        self.check_user_permission()
        
        todo_list = data.get('todo_list')
        if todo_list and todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на создание задач в этом списке")
    
    def validate_update_permissions(self, instance: Task, data: Dict[str, Any]) -> None:
        """Проверка прав на обновление задачи."""
        self.check_user_permission()
        
        if instance.todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на изменение этой задачи")
    
    def validate_delete_permissions(self, instance: Task) -> None:
        """Проверка прав на удаление задачи."""
        self.check_user_permission()
        
        if instance.todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на удаление этой задачи")
    
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при создании."""
        # Проверяем обязательные поля
        if not data.get('title', '').strip():
            raise ValidationError("Название задачи не может быть пустым")
        
        if len(data.get('title', '')) > 200:
            raise ValidationError("Название задачи слишком длинное (максимум 200 символов)")
        
        # Валидируем теги
        if 'tag_ids' in data:
            self._validate_tags(data.get('todo_list'), data['tag_ids'])
        
        return data
    
    def validate_update_data(self, instance: Task, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при обновлении."""
        if 'title' in data and not data['title'].strip():
            raise ValidationError("Название задачи не может быть пустым")
        
        if 'title' in data and len(data['title']) > 200:
            raise ValidationError("Название задачи слишком длинное (максимум 200 символов)")
        
        # Валидируем теги
        if 'tag_ids' in data:
            todo_list = data.get('todo_list', instance.todo_list)
            self._validate_tags(todo_list, data['tag_ids'])
        
        return data
    
    def _validate_tags(self, todo_list: TodoList, tag_ids: List[int]) -> None:
        """Проверяем, что теги принадлежат списку."""
        if tag_ids:
            invalid_tags = Tag.objects.filter(
                id__in=tag_ids
            ).exclude(todo_list=todo_list)
            
            if invalid_tags.exists():
                raise ValidationError("Некоторые теги не принадлежат этому списку")
    

    """
    Декоратор transaction - это декоратор, который позволяет выполнить запрос в БД, который 
    требует выполнения в одной транзакции. 
    """
    @transaction.atomic
    def mark_done(self, task: Task) -> Task:
        """
        Пометить задачу как выполненную.
        ЭТО ЛОГИКА, КОТОРУЮ УБРАЛИ ИЗ МОДЕЛИ!
        """
        self.validate_update_permissions(task, {})
        
        if task.status == Task.Status.DONE:
            return task  # Уже выполнена
        
        task.status = Task.Status.DONE
        task.completed_at = timezone.now()  # Автоматически заполняем
        task.save()
        
        return task
    
    @transaction.atomic
    def mark_todo(self, task: Task) -> Task:
        """Вернуть задачу в работу."""
        self.validate_update_permissions(task, {})
        
        task.status = Task.Status.TODO
        task.completed_at = None  # Сбрасываем дату завершения
        task.save()
        
        return task
    
    @transaction.atomic
    def mark_in_progress(self, task: Task) -> Task:
        """Пометить задачу как выполняющуюся."""
        self.validate_update_permissions(task, {})
        
        task.status = Task.Status.IN_PROGRESS
        task.completed_at = None
        task.save()
        
        return task
    
    @transaction.atomic
    def mark_blocked(self, task: Task) -> Task:
        """Заблокировать задачу."""
        self.validate_update_permissions(task, {})
        
        task.status = Task.Status.BLOCKED
        task.completed_at = None
        task.save()
        
        return task
    
    @transaction.atomic
    def toggle_favorite(self, task: Task) -> Task:
        """Переключить избранное."""
        self.validate_update_permissions(task, {})
        
        task.is_favorite = not task.is_favorite
        task.save()
        
        return task
    
    @transaction.atomic
    def assign_to_user(self, task: Task, assignee_id: Optional[int]) -> Task:
        """Назначить исполнителя."""
        self.validate_update_permissions(task, {})
        
        task.assignee_id = assignee_id
        task.save()
        
        return task
    
    @transaction.atomic
    def set_due_date(self, task: Task, due_date: Optional[timezone.datetime]) -> Task:
        """Установить дедлайн."""
        self.validate_update_permissions(task, {})
        
        # Валидация: дедлайн не в прошлом для незавершенных задач
        if (due_date and due_date < timezone.now() 
            and task.status != Task.Status.DONE):
            raise ValidationError("Дедлайн не может быть в прошлом для незавершенной задачи")
        
        task.due_date = due_date
        task.save()
        
        return task
    
    @transaction.atomic
    def bulk_mark_done(self, task_ids: List[int]) -> List[Task]:
        """Массовое завершение задач."""
        tasks = self.get_user_queryset().filter(id__in=task_ids)
        completed_tasks = []
        
        for task in tasks:
            try:
                completed_task = self.mark_done(task)
                completed_tasks.append(completed_task)
            except (PermissionDenied, ValidationError):
                # Пропускаем задачи, которые нельзя завершить
                continue
        
        return completed_tasks
    
    @transaction.atomic
    def bulk_update_status(self, task_ids: List[int], status: str) -> List[Task]:
        """Массовое обновление статуса."""
        if status not in [choice[0] for choice in Task.Status.choices]:
            raise ValidationError(f"Недопустимый статус: {status}")
        
        tasks = self.get_user_queryset().filter(id__in=task_ids)
        updated_tasks = []
        
        for task in tasks:
            try:
                # Используем соответствующий метод для каждого статуса
                if status == Task.Status.DONE:
                    updated_task = self.mark_done(task)
                elif status == Task.Status.TODO:
                    updated_task = self.mark_todo(task)
                elif status == Task.Status.IN_PROGRESS:
                    updated_task = self.mark_in_progress(task)
                elif status == Task.Status.BLOCKED:
                    updated_task = self.mark_blocked(task)
                else:
                    # Прямое обновление для других статусов
                    task.status = status
                    if status == Task.Status.DONE:
                        task.completed_at = timezone.now()
                    else:
                        task.completed_at = None
                    task.save()
                    updated_task = task
                
                updated_tasks.append(updated_task)
            except (PermissionDenied, ValidationError):
                continue
        
        return updated_tasks
    
    def _perform_create(self, validated_data: Dict[str, Any]) -> Task:
        """Создание задачи с обработкой тегов."""
        tag_ids = validated_data.pop('tag_ids', [])
        
        task = super()._perform_create(validated_data)
        
        # Устанавливаем теги
        if tag_ids:
            task.tags.set(tag_ids)
        
        return task
    
    def _perform_update(self, instance: Task, validated_data: Dict[str, Any]) -> Task:
        """Обновление задачи с обработкой тегов и completed_at."""
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Обновляем поля
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        # ЛОГИКА ИЗ СТАРОГО save() МЕТОДА:
        # Автоматически заполняем/сбрасываем completed_at
        if instance.status == Task.Status.DONE and instance.completed_at is None:
            instance.completed_at = timezone.now()
        elif instance.status != Task.Status.DONE:
            instance.completed_at = None
        
        instance.save()
        
        # Обновляем теги
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Получить статистику задач пользователя."""
        tasks = self.get_user_queryset()
        
        stats = {
            'total': tasks.count(),
            'todo': tasks.filter(status=Task.Status.TODO).count(),
            'in_progress': tasks.filter(status=Task.Status.IN_PROGRESS).count(),
            'done': tasks.filter(status=Task.Status.DONE).count(),
            'blocked': tasks.filter(status=Task.Status.BLOCKED).count(),
            'overdue': self.get_overdue_tasks().count(),
            'high_priority': self.get_high_priority_tasks().count(),
            'favorites': tasks.filter(is_favorite=True).count(),
        }
        
        return stats
