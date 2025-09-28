# apps/todos/serializers.py
from __future__ import annotations

from typing import Any, Iterable, Sequence

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import TodoList, Tag, Task, Comment

User = get_user_model()


# ===== Базовые сериализаторы пользователей (минимум для ссылок) =====
class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


# ===== Tag =====
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "todo_list", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


# ===== Comment =====
class CommentWriteSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Comment
        fields = ("id", "task", "author", "text", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class CommentSerializer(CommentWriteSerializer):
    author = UserMiniSerializer(read_only=True)


# ===== Task =====
class TaskReadSerializer(serializers.ModelSerializer):
    assignee = UserMiniSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_overdue = serializers.SerializerMethodField()
    is_done = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id",
            "todo_list",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "due_date",
            "completed_at",
            "tags",
            "is_favorite",
            "is_overdue",
            "is_done",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "completed_at", "created_at", "updated_at")

    def get_is_overdue(self, obj: Task) -> bool:
        return bool(obj.due_date and obj.status != Task.Status.DONE and obj.due_date < timezone.now())

    def get_is_done(self, obj: Task) -> bool:
        return obj.status == Task.Status.DONE


class TaskWriteSerializer(serializers.ModelSerializer):
    # для записи — ID вместо вложенных объектов
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), write_only=True, required=False
    )
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "todo_list",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "due_date",
            "completed_at",
            "tag_ids",
            "is_favorite",
        )
        read_only_fields = ("id", "completed_at")

    # --- Валидации ---
    def validate_due_date(self, value):
        # Разрешим прошлые дедлайны, но можно включить проверку при необходимости:
        # if value and value < timezone.now():
        #     raise serializers.ValidationError("Срок не может быть в прошлом.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        todo_list: TodoList = attrs.get("todo_list") or getattr(self.instance, "todo_list", None)
        tag_ids: Sequence[Tag] | None = attrs.get("tag_ids")

        # Проверка: все теги принадлежат тому же списку
        if todo_list and tag_ids:
            invalid = [t.id for t in tag_ids if t.todo_list_id != todo_list.id]
            if invalid:
                raise serializers.ValidationError(
                    {"tag_ids": f"Некоторые теги не принадлежат списку {todo_list.id}: {invalid}"}
                )

        # Если статус DONE — completed_at выставляем автоматически в save(), не здесь
        return attrs

    # --- CRUD ---
    def _set_relations(self, instance: Task, validated_data: dict[str, Any]):
        if "assignee_id" in validated_data:
            instance.assignee = validated_data.get("assignee_id")
        if "tag_ids" in validated_data:
            tags: Iterable[Tag] = validated_data.get("tag_ids") or []
            instance.tags.set(tags)

    def create(self, validated_data: dict[str, Any]) -> Task:
        tag_ids = validated_data.pop("tag_ids", None)
        assignee = validated_data.pop("assignee_id", None)

        task = Task.objects.create(**validated_data)
        if assignee is not None:
            task.assignee = assignee
            task.save(update_fields=["assignee", "updated_at"])
        if tag_ids is not None:
            task.tags.set(tag_ids)
        return task

    def update(self, instance: Task, validated_data: dict[str, Any]) -> Task:
        tag_ids = validated_data.pop("tag_ids", None)
        assignee = validated_data.pop("assignee_id", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if assignee is not None:
            instance.assignee = assignee
        instance.save()  # триггерит логику completed_at в модели

        if tag_ids is not None:
            instance.tags.set(tag_ids)

        return instance


# ===== TodoList =====
class TodoListReadSerializer(serializers.ModelSerializer):
    owner = UserMiniSerializer(read_only=True)
    tasks_count = serializers.IntegerField(read_only=True)
    open_tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = TodoList
        fields = (
            "id",
            "owner",
            "title",
            "description",
            "is_archived",
            "tasks_count",
            "open_tasks_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "tasks_count", "open_tasks_count")

    def get_open_tasks_count(self, obj: TodoList) -> int:
        return obj.tasks.exclude(status=Task.Status.DONE).count()


class TodoListWriteSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TodoList
        fields = ("id", "owner", "title", "description", "is_archived", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
