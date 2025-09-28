from django.conf import settings
from django.db import models

from .base import TimeStampedModel


class TodoList(TimeStampedModel):
    """Список задач - ТОЛЬКО СХЕМА БД (Anemic Model)."""
    
    # если мы захотим взять owner у Task, то мы можем сделать это так:
    """
    tasks = Task.objects.select_related('todo_list')
    .prefetch_related('tags')
    .all()

    Если предположить что user, который у нас в параметрах это и есть owner

    если у нас есть информация о owner, то дальше уже 
    мы можем взять owner из todo_list

    for task in tasks:
        if task.todo_list.owner == user:
            print(task.title)

    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="todo_lists",
    )
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "is_archived"]),
        ]
        unique_together = [("owner", "title")]

    def __str__(self):
        return self.title

    # НИКАКИХ МЕТОДОВ БИЗНЕС-ЛОГИКИ!
    # Вся логика архивирования, валидации и т.д. будет в сервисах
