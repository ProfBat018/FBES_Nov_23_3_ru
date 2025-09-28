from django.conf import settings
from django.db import models

from .base import TimeStampedModel


class Task(TimeStampedModel):
    """Задача - ТОЛЬКО СХЕМА БД (Anemic Model)."""
    
    # Чтобы реализовать функционал как в enum, мы наследуемся от models.TextChoices
    class Status(models.TextChoices):
        TODO = "todo", "К выполнению"
        IN_PROGRESS = "in_progress", "В работе"
        DONE = "done", "Готово"
        BLOCKED = "blocked", "Заблокировано"

    class Priority(models.IntegerChoices):
        LOW = 1, "Низкий"
        MEDIUM = 2, "Средний"
        HIGH = 3, "Высокий"
        CRITICAL = 4, "Критичный"

    # ТОЛЬКО поля БД - никакой логики
    todo_list = models.ForeignKey(
        'TodoList',  # Forward reference, так как модели в разных файлах
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        db_index=True,
    )
    priority = models.IntegerField(
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)  # Заполняется сервисом
    tags = models.ManyToManyField('Tag', blank=True, related_name="tasks")
    is_favorite = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_favorite", "priority", "created_at"]
        indexes = [
            models.Index(fields=["todo_list", "status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["assignee"]),
        ]

    def __str__(self):
        return self.title

    # УБРАЛИ ВСЮ БИЗНЕС-ЛОГИКУ:
    # - mark_done() метод удален
    # - save() логика удалена
    # - Никаких методов валидации
    # 
    # Теперь это чистая Anemic Model - только схема БД!
