# Глобальный импорт всех ViewSets для удобного использования

from .task_viewset import TaskViewSet
from .todolist_viewset import TodoListViewSet
from .tag_viewset import TagViewSet
from .comment_viewset import CommentViewSet

# Экспортируем все ViewSets
__all__ = [
    'TaskViewSet',
    'TodoListViewSet',
    'TagViewSet',
    'CommentViewSet',
]
