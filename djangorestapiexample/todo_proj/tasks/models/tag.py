from django.db import models

from .base import TimeStampedModel


class Tag(TimeStampedModel):
    """Теги для задач - ТОЛЬКО СХЕМА БД (Anemic Model)."""
    
    name = models.CharField(max_length=40)
    color = models.CharField(max_length=7, blank=True, help_text="#RRGGBB")
    todo_list = models.ForeignKey(
        'TodoList',  # Forward reference
        on_delete=models.CASCADE,
        related_name="tags",
    )

    class Meta:
        # Уникальность тега в списке
        unique_together = [("todo_list", "name")]
        ordering = ["name"]

    def __str__(self):
        return self.name

    # НИКАКИХ МЕТОДОВ БИЗНЕС-ЛОГИКИ!
    # Вся логика валидации цвета, уникальности и т.д. будет в сервисах
