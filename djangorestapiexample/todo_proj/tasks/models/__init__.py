# Глобальный импорт всех моделей для удобного использования
# Теперь можно импортировать: from todo_proj.tasks.models import Task, TodoList, Tag, Comment

from .base import TimeStampedModel
from .todo_list import TodoList
from .task import Task
from .tag import Tag
from .comment import Comment

# Экспортируем все модели. Тоже самое как и module.exports в Node.js
__all__ = [
    'TimeStampedModel',
    'TodoList', 
    'Task',
    'Tag',
    'Comment',
]
