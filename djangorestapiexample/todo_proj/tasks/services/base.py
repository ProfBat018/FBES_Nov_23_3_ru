from abc import ABC
from typing import Type, Optional, Dict, Any
from django.db import models, transaction
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied, ValidationError

User = get_user_model()

# ABC - Abstract Base Class
class BaseService(ABC):
    """Базовый класс для всех сервисов с общей логикой."""
    
    """
    Несмотря на то, что пайтон нестроготипизованный я могу указать чтобы 
    мои модели были models.Model
    """
    model: Type[models.Model] = None
    
    def __init__(self, user: Optional[User] = None):
        self.user = user
    

    def get_queryset(self) -> models.QuerySet:
        """Базовый queryset для модели."""
        if not self.model:
            raise NotImplementedError("Model должен быть определен в наследнике")
        return self.model.objects.all()
    
    def get_user_queryset(self) -> models.QuerySet:
        """Queryset с фильтрацией по пользователю (переопределить в наследниках)."""
        return self.get_queryset()
    
    @transaction.atomic
    def create(self, data: Dict[str, Any]) -> models.Model:
        """Создание объекта с валидацией."""
        self.validate_create_permissions(data)
        validated_data = self.validate_create_data(data)
        return self._perform_create(validated_data)
    
    @transaction.atomic
    def update(self, instance: models.Model, data: Dict[str, Any]) -> models.Model:
        """Обновление объекта с валидацией."""
        self.validate_update_permissions(instance, data)
        validated_data = self.validate_update_data(instance, data)
        return self._perform_update(instance, validated_data)
    
    @transaction.atomic
    def delete(self, instance: models.Model) -> None:
        """Удаление объекта с проверкой прав."""
        self.validate_delete_permissions(instance)
        self._perform_delete(instance)
    
    # Методы для переопределения в наследниках
    def validate_create_permissions(self, data: Dict[str, Any]) -> None:
        """Проверка прав на создание."""
        pass
    
    def validate_update_permissions(self, instance: models.Model, data: Dict[str, Any]) -> None:
        """Проверка прав на обновление."""
        pass
    
    def validate_delete_permissions(self, instance: models.Model) -> None:
        """Проверка прав на удаление."""
        pass
    
    def validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при создании."""
        return data
    
    def validate_update_data(self, instance: models.Model, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных при обновлении."""
        return data
    
    def _perform_create(self, validated_data: Dict[str, Any]) -> models.Model:
        """Выполнение создания."""
        return self.model.objects.create(**validated_data)
    
    def _perform_update(self, instance: models.Model, validated_data: Dict[str, Any]) -> models.Model:
        """Выполнение обновления."""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
    
    def _perform_delete(self, instance: models.Model) -> None:
        """Выполнение удаления."""
        instance.delete()
    
    def check_user_permission(self, message: str = "Нет прав доступа") -> None:
        """Проверка, что пользователь авторизован."""
        if not self.user:
            raise PermissionDenied(message)

