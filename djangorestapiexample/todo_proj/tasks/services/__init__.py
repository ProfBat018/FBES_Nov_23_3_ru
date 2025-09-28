# Глобальный импорт всех сервисов для удобного использования
# Теперь можно импортировать: from todo_proj.tasks.services import TaskService, TodoListService

from .base import BaseService
from .task_service import TaskService
from .todolist_service import TodoListService
from .tag_service import TagService
from .comment_service import CommentService

# Экспортируем все сервисы
__all__ = [
    'BaseService',
    'TaskService',
    'TodoListService', 
    'TagService',
    'CommentService',
]
