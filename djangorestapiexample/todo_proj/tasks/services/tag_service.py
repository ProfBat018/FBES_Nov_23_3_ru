import re
from typing import Dict, Any
from django.db.models import QuerySet
from django.db import transaction
from django.db.models import Count
from rest_framework.exceptions import PermissionDenied, ValidationError

from .base import BaseService
from ..models import Tag, TodoList


class TagService(BaseService):
    """Сервис для работы с тегами."""
    
    model = Tag
    
    def get_user_queryset(self) -> QuerySet:
        """Теги из списков пользователя."""
        self.check_user_permission()
        return self.model.objects.filter(
            todo_list__owner=self.user
        ).select_related('todo_list')
    
    def get_list_tags(self, todo_list: TodoList) -> QuerySet:
        """Теги конкретного списка."""
        self.check_user_permission()
        
        if todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на просмотр тегов этого списка")
        
        return self.model.objects.filter(todo_list=todo_list)
    
    def validate_create_permissions(self, data: Dict[str, Any]) -> None:
        """Проверка прав на создание тега."""
        self.check_user_permission()
        
        todo_list = data.get('todo_list')
        if todo_list and todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на создание тегов в этом списке")
    
    def validate_update_permissions(self, instance: Tag, data: Dict[str, Any]) -> None:
        """Проверка прав на обновление тега."""
        self.check_user_permission()
        
        if instance.todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на изменение этого тега")
    
    def validate_delete_permissions(self, instance: Tag) -> None:
        """Проверка прав на удаление тега."""
        self.check_user_permission()
        
        if instance.todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на удаление этого тега")
    
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при создании."""
        # Проверяем обязательные поля
        if not data.get('name', '').strip():
            raise ValidationError("Название тега не может быть пустым")
        
        name = data['name'].strip()
        if len(name) > 40:
            raise ValidationError("Название тега слишком длинное (максимум 40 символов)")
        
        # Проверяем уникальность в рамках списка
        todo_list = data.get('todo_list')
        if todo_list and self.model.objects.filter(
            todo_list=todo_list, 
            name=name
        ).exists():
            raise ValidationError("Тег с таким названием уже существует в этом списке")
        
        # Валидируем цвет
        color = data.get('color', '').strip()
        if color:
            if not self._is_valid_color(color):
                raise ValidationError("Неверный формат цвета. Используйте формат #RRGGBB")
            data['color'] = color.upper()  # Приводим к верхнему регистру
        
        data['name'] = name
        return data
    
    def validate_update_data(self, instance: Tag, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при обновлении."""
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                raise ValidationError("Название тега не может быть пустым")
            
            if len(name) > 40:
                raise ValidationError("Название тега слишком длинное (максимум 40 символов)")
            
            # Проверяем уникальность (кроме текущего тега)
            if self.model.objects.filter(
                todo_list=instance.todo_list,
                name=name
            ).exclude(id=instance.id).exists():
                raise ValidationError("Тег с таким названием уже существует в этом списке")
            
            data['name'] = name
        
        # Валидируем цвет
        if 'color' in data:
            color = data['color'].strip()
            if color:
                if not self._is_valid_color(color):
                    raise ValidationError("Неверный формат цвета. Используйте формат #RRGGBB")
                data['color'] = color.upper()
            else:
                data['color'] = ''  # Разрешаем пустой цвет
        
        return data
    
    def _is_valid_color(self, color: str) -> bool:
        """Проверка валидности HEX цвета."""
        if not color:
            return True  # Пустой цвет разрешен
        
        # Проверяем формат #RRGGBB
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        return bool(hex_pattern.match(color))
    
    @transaction.atomic
    def create_default_tags(self, todo_list: TodoList) -> list[Tag]:
        """Создать набор тегов по умолчанию для нового списка."""
        if todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на создание тегов в этом списке")
        
        default_tags = [
            {'name': 'Важно', 'color': '#FF5722'},
            {'name': 'Срочно', 'color': '#F44336'},
            {'name': 'Работа', 'color': '#2196F3'},
            {'name': 'Личное', 'color': '#4CAF50'},
        ]
        
        created_tags = []
        for tag_data in default_tags:
            # Проверяем, что тег с таким названием не существует
            if not self.model.objects.filter(
                todo_list=todo_list,
                name=tag_data['name']
            ).exists():
                tag = self.model.objects.create(
                    todo_list=todo_list,
                    **tag_data
                )
                created_tags.append(tag)
        
        return created_tags
    
    @transaction.atomic
    def bulk_delete_unused_tags(self, todo_list: TodoList) -> int:
        """Удалить неиспользуемые теги из списка."""
        if todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на удаление тегов из этого списка")
        
        # Находим теги без задач
        unused_tags = self.model.objects.filter(
            todo_list=todo_list,
            tasks__isnull=True
        )
        
        count = unused_tags.count()
        unused_tags.delete()
        
        return count
    
    def get_tag_usage_statistics(self, todo_list: TodoList) -> Dict[str, Any]:
        """Получить статистику использования тегов в списке."""
        if todo_list.owner != self.user:
            raise PermissionDenied("Нет прав на просмотр статистики этого списка")
        
        tags = self.get_list_tags(todo_list).annotate(
            tasks_count=Count('tasks')
        )
        
        stats = {
            'total_tags': tags.count(),
            'used_tags': tags.filter(tasks_count__gt=0).count(),
            'unused_tags': tags.filter(tasks_count=0).count(),
            'most_used_tag': None,
            'tag_usage': []
        }
        
        # Детальная статистика по каждому тегу
        for tag in tags:
            tag_info = {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'tasks_count': tag.tasks_count,
            }
            stats['tag_usage'].append(tag_info)
        
        # Самый используемый тег
        most_used = tags.filter(tasks_count__gt=0).order_by('-tasks_count').first()
        if most_used:
            stats['most_used_tag'] = {
                'name': most_used.name,
                'tasks_count': most_used.tasks_count
            }
        
        return stats
