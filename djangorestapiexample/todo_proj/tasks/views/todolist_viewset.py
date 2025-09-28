from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.exceptions import ValidationError, PermissionDenied

from ..models import TodoList
from ..serializers import TodoListReadSerializer, TodoListWriteSerializer
from ..services import TodoListService
from ..permissions import IsOwner


class TodoListViewSet(viewsets.ModelViewSet):
    """ViewSet для управления списками задач с использованием TodoListService."""
    
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._todolist_service = None
    
    @property
    def todolist_service(self) -> TodoListService:
        """Ленивая инициализация сервиса с текущим пользователем."""
        if self._todolist_service is None:
            self._todolist_service = TodoListService(user=getattr(self.request, 'user', None))
        return self._todolist_service
    
    def get_queryset(self):
        """Используем сервис для получения queryset."""
        return self.todolist_service.get_user_queryset()
    
    def get_serializer_class(self):
        """Разные сериализаторы для чтения и записи."""
        if self.action in ['create', 'update', 'partial_update']:
            return TodoListWriteSerializer
        return TodoListReadSerializer
    
    def create(self, request, *args, **kwargs):
        """Создание списка через сервис."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            todo_list = self.todolist_service.create(serializer.validated_data)
            response_serializer = TodoListReadSerializer(todo_list)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Обновление списка через сервис."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            todo_list = self.todolist_service.update(instance, serializer.validated_data)
            response_serializer = TodoListReadSerializer(todo_list)
            return Response(response_serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Удаление списка через сервис."""
        instance = self.get_object()
        try:
            self.todolist_service.delete(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Архивировать список."""
        todo_list = self.get_object()
        try:
            archived_list = self.todolist_service.archive_list(todo_list)
            serializer = TodoListReadSerializer(archived_list)
            return Response(serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Разархивировать список."""
        todo_list = self.get_object()
        try:
            unarchived_list = self.todolist_service.unarchive_list(todo_list)
            serializer = TodoListReadSerializer(unarchived_list)
            return Response(serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def archived(self, request):
        """Получить архивированные списки."""
        try:
            queryset = self.todolist_service.get_archived_lists()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = TodoListReadSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = TodoListReadSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Получить активные списки."""
        try:
            queryset = self.todolist_service.get_active_lists()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = TodoListReadSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = TodoListReadSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Дублировать список со всеми задачами и тегами."""
        todo_list = self.get_object()
        new_title = request.data.get('title')
        
        if not new_title:
            return Response(
                {'error': 'Необходимо указать новое название списка'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            duplicated_list = self.todolist_service.duplicate_list(todo_list, new_title)
            serializer = TodoListReadSerializer(duplicated_list)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Получить статистику конкретного списка."""
        todo_list = self.get_object()
        try:
            stats = self.todolist_service.get_list_statistics(todo_list)
            return Response(stats)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def user_statistics(self, request):
        """Получить общую статистику списков пользователя."""
        try:
            stats = self.todolist_service.get_user_statistics()
            return Response(stats)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
