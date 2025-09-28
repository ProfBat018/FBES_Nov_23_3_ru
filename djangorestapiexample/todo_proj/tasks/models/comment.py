from django.conf import settings
from django.db import models

from .base import TimeStampedModel


class Comment(TimeStampedModel):
    """Комментарии к задачам - ТОЛЬКО СХЕМА БД (Anemic Model)."""
    
    # Внешний ключ на Task
    task = models.ForeignKey(
        'Task',  # Forward reference
        on_delete=models.CASCADE, 
        related_name="comments"
    )
    # Внешний ключ на User
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_comments",
    )
    # Текст комментария
    text = models.TextField()

    # Метаданные, ordering отвечает за сортировку комментариев 
    class Meta:
        ordering = ["created_at"]

    # ToString 
    def __str__(self):
        return f"Комментарий к «{self.task}» от {self.author}"

    # НИКАКИХ МЕТОДОВ БИЗНЕС-ЛОГИКИ!
    # Вся логика валидации текста, прав доступа и т.д. будет в сервисах
