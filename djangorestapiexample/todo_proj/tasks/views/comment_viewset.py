from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError, PermissionDenied

from ..models import Comment, Task
from ..serializers import CommentSerializer, CommentWriteSerializer
from ..services import CommentService


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet для управления комментариями с использованием CommentService."""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['text']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['created_at']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._comment_service = None
    
    @property
    def comment_service(self) -> CommentService:
        """Ленивая инициализация сервиса с текущим пользователем."""
        if self._comment_service is None:
            self._comment_service = CommentService(user=getattr(self.request, 'user', None))
        return self._comment_service
    
    def get_queryset(self):
        """Используем сервис для получения queryset."""
        return self.comment_service.get_user_queryset()
    
    def get_serializer_class(self):
        """Разные сериализаторы для чтения и записи."""
        if self.action in ['create', 'update', 'partial_update']:
            return CommentWriteSerializer
        return CommentSerializer
    
    def create(self, request, *args, **kwargs):
        """Создание комментария через сервис."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            comment = self.comment_service.create(serializer.validated_data)
            response_serializer = CommentSerializer(comment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Обновление комментария через сервис."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            comment = self.comment_service.update(instance, serializer.validated_data)
            response_serializer = CommentSerializer(comment)
            return Response(response_serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Удаление комментария через сервис."""
        instance = self.get_object()
        try:
            self.comment_service.delete(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def task_comments(self, request):
        """Получить комментарии к конкретной задаче."""
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response(
                {'error': 'Необходимо указать task_id в query параметрах'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task = Task.objects.get(id=task_id)
            queryset = self.comment_service.get_task_comments(task)
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = CommentSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = CommentSerializer(queryset, many=True)
            return Response(serializer.data)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Задача не найдена'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_comments(self, request):
        """Получить комментарии, написанные текущим пользователем."""
        try:
            queryset = self.comment_service.get_user_comments()
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = CommentSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = CommentSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Получить последние комментарии."""
        limit = int(request.query_params.get('limit', 10))
        try:
            queryset = self.comment_service.get_recent_comments(limit)
            serializer = CommentSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Поиск по комментариям."""
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'error': 'Необходимо указать параметр q для поиска'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            queryset = self.comment_service.search_comments(query)
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = CommentSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = CommentSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Получить статистику комментариев пользователя."""
        try:
            stats = self.comment_service.get_comment_statistics()
            return Response(stats)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def add_to_task(self, request):
        """Быстро добавить комментарий к задаче."""
        task_id = request.data.get('task_id')
        text = request.data.get('text')
        
        if not task_id or not text:
            return Response(
                {'error': 'Необходимы task_id и text'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task = Task.objects.get(id=task_id)
            comment = self.comment_service.create_comment(task, text)
            serializer = CommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Задача не найдена'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
