from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError, PermissionDenied

from ..models import Tag, TodoList
from ..serializers import TagSerializer
from ..services import TagService
from ..permissions import IsOwner


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet для управления тегами с использованием TagService."""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['name']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tag_service = None
    
    @property
    def tag_service(self) -> TagService:
        """Ленивая инициализация сервиса с текущим пользователем."""
        if self._tag_service is None:
            self._tag_service = TagService(user=getattr(self.request, 'user', None))
        return self._tag_service
    
    def get_queryset(self):
        """Используем сервис для получения queryset."""
        return self.tag_service.get_user_queryset()
    
    def get_serializer_class(self):
        """Используем один сериализатор для тегов."""
        return TagSerializer
    
    def create(self, request, *args, **kwargs):
        """Создание тега через сервис."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            tag = self.tag_service.create(serializer.validated_data)
            response_serializer = TagSerializer(tag)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Обновление тега через сервис."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            tag = self.tag_service.update(instance, serializer.validated_data)
            response_serializer = TagSerializer(tag)
            return Response(response_serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Удаление тега через сервис."""
        instance = self.get_object()
        try:
            self.tag_service.delete(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def create_defaults(self, request):
        """Создать теги по умолчанию для списка."""
        todo_list_id = request.data.get('todo_list_id')
        if not todo_list_id:
            return Response(
                {'error': 'Необходимо указать todo_list_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            todo_list = TodoList.objects.get(id=todo_list_id, owner=request.user)
            created_tags = self.tag_service.create_default_tags(todo_list)
            serializer = TagSerializer(created_tags, many=True)
            return Response({
                'created_count': len(created_tags),
                'tags': serializer.data
            }, status=status.HTTP_201_CREATED)
        except TodoList.DoesNotExist:
            return Response(
                {'error': 'Список задач не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def cleanup_unused(self, request):
        """Удалить неиспользуемые теги из списка."""
        todo_list_id = request.data.get('todo_list_id')
        if not todo_list_id:
            return Response(
                {'error': 'Необходимо указать todo_list_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            todo_list = TodoList.objects.get(id=todo_list_id, owner=request.user)
            deleted_count = self.tag_service.bulk_delete_unused_tags(todo_list)
            return Response({
                'deleted_count': deleted_count,
                'message': f'Удалено {deleted_count} неиспользуемых тегов'
            })
        except TodoList.DoesNotExist:
            return Response(
                {'error': 'Список задач не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def list_tags(self, request):
        """Получить теги конкретного списка."""
        todo_list_id = request.query_params.get('todo_list_id')
        if not todo_list_id:
            return Response(
                {'error': 'Необходимо указать todo_list_id в query параметрах'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            todo_list = TodoList.objects.get(id=todo_list_id, owner=request.user)
            queryset = self.tag_service.get_list_tags(todo_list)
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = TagSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = TagSerializer(queryset, many=True)
            return Response(serializer.data)
        except TodoList.DoesNotExist:
            return Response(
                {'error': 'Список задач не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def usage_statistics(self, request):
        """Получить статистику использования тегов в списке."""
        todo_list_id = request.query_params.get('todo_list_id')
        if not todo_list_id:
            return Response(
                {'error': 'Необходимо указать todo_list_id в query параметрах'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            todo_list = TodoList.objects.get(id=todo_list_id, owner=request.user)
            stats = self.tag_service.get_tag_usage_statistics(todo_list)
            return Response(stats)
        except TodoList.DoesNotExist:
            return Response(
                {'error': 'Список задач не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
