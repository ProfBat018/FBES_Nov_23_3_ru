from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Task
from ..serializers import TaskReadSerializer, TaskWriteSerializer
from ..services import TaskService
from ..permissions import IsOwner

"""
ViewSet, если сравнивать с ASP.NET Core, то это Controller. 
В этом классе мы определяем методы, которые будут обрабатывать запросы.
"""


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet для управления задачами с использованием TaskService."""
    
    # Permission classes - это классы, которые определяют права доступа к методам. cfvb permissions
    # указаны в settings.py
    permission_classes = [IsAuthenticated]

    # Filter backends - это классы, которые определяют фильтры для запросов.
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Search fields - это поля, по которым можно искать.
    search_fields = ['title', 'description']

    # Ordering fields - это поля, по которым можно сортировать.
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']

    # Ordering - значения, по которым идет сортировка.
    ordering = ['-is_favorite', 'priority', 'created_at']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._task_service = None
    

    """
    Ленивая инициализация сервиса с текущим пользователем.
    Если сервис не был инициализирован, то инициализируем его.
    """
    @property
    def task_service(self) -> TaskService:
        """Ленивая инициализация сервиса с текущим пользователем."""
        if self._task_service is None:
            self._task_service = TaskService(user=getattr(self.request, 'user', None))
        return self._task_service
    
    """
    Метод, который используется для получения queryset.
    """
    def get_queryset(self):
        """Используем сервис для получения queryset."""
        return self.task_service.get_user_queryset()
    
    """
    В целом вы должны понять что сериализаторы используются для понимания со стороны 
    Back-End ваших данных из json формата. Такое поведение в целом не бывает в ASP.NET, 
    потому что kestrel сам понимает как сериализовать и десериализовать данные. В пайтоне 
    такого нет, потому что тут нет рефлексии.
    """
    def get_serializer_class(self):
        """Разные сериализаторы для чтения и записи."""
        if self.action in ['create', 'update', 'partial_update']:
            return TaskWriteSerializer
        return TaskReadSerializer
    
    """
    Метод, который используется для создания задачи.
    """
    @swagger_auto_schema(
        operation_description="Создание новой задачи",
        operation_summary="Создать задачу",
        request_body=TaskWriteSerializer,
        responses={
            201: openapi.Response('Задача создана', TaskReadSerializer),
            400: 'Ошибка валидации'
        }
    )
    def create(self, request, *args, **kwargs):
        """Создание задачи через сервис."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            task = self.task_service.create(serializer.validated_data)
            response_serializer = TaskReadSerializer(task)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Обновление существующей задачи",
        operation_summary="Обновить задачу",
        request_body=TaskWriteSerializer,
        responses={
            200: openapi.Response('Задача обновлена', TaskReadSerializer),
            400: 'Ошибка валидации',
            404: 'Задача не найдена'
        }
    )
    def update(self, request, *args, **kwargs):
        """Обновление задачи через сервис."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            task = self.task_service.update(instance, serializer.validated_data)
            response_serializer = TaskReadSerializer(task)
            return Response(response_serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Удаление задачи",
        operation_summary="Удалить задачу",
        responses={
            204: 'Задача удалена',
            404: 'Задача не найдена'
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Удаление задачи через сервис."""
        instance = self.get_object()
        try:
            self.task_service.delete(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

    """
    Декоратор action - это декоратор, который позволяет определить метод, который будет 
    обрабатывать запрос.
    В ASP.NET Core это атрибут [HttpPost("mark_done")] в котором мы указываем путь и метод.

    detail=True - это означает, что метод будет обрабатывать запрос к конкретной задаче.
    methods=['post'] - это означает, что метод будет обрабатывать запрос методом POST.

    basename - the base to use for the URL names that are created.
    basename, пишется если вы не создаете urls.py файл.

    action - the name of the current action (e.g., list, create).
    detail - boolean indicating if the current action is configured for a list or detail view.
    suffix - the display suffix for the viewset type - mirrors the detail attribute.
    name - the display name for the viewset. This argument is mutually exclusive to suffix.
    description - the display description for the individual view of a viewset.

    """
    @swagger_auto_schema(
        method='post',
        operation_description="Отметить задачу как выполненную",
        operation_summary="Завершить задачу",
        responses={
            200: openapi.Response('Задача отмечена как выполненная', TaskReadSerializer),
            404: 'Задача не найдена'
        }
    )
    @action(detail=True, methods=['post'])
    def mark_done(self, request, pk=None):
        """Пометить задачу как выполненную - используем сервис вместо модели."""
        task = self.get_object()
        try:
            completed_task = self.task_service.mark_done(task)
            serializer = TaskReadSerializer(completed_task)
            return Response(serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def mark_todo(self, request, pk=None):
        """Вернуть задачу в работу."""
        task = self.get_object()
        try:
            todo_task = self.task_service.mark_todo(task)
            serializer = TaskReadSerializer(todo_task)
            return Response(serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def mark_in_progress(self, request, pk=None):
        """Пометить задачу как выполняющуюся."""
        task = self.get_object()
        try:
            in_progress_task = self.task_service.mark_in_progress(task)
            serializer = TaskReadSerializer(in_progress_task)
            return Response(serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Переключить статус избранной задачи",
        operation_summary="Добавить/убрать из избранного",
        responses={
            200: openapi.Response('Статус избранного изменен', TaskReadSerializer),
            404: 'Задача не найдена'
        }
    )
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Переключить избранное."""
        task = self.get_object()
        try:
            updated_task = self.task_service.toggle_favorite(task)
            serializer = TaskReadSerializer(updated_task)
            return Response(serializer.data)
        except (ValidationError, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Задачи, назначенные на текущего пользователя."""
        try:
            queryset = self.task_service.get_assigned_tasks()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = TaskReadSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = TaskReadSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Просроченные задачи."""
        try:
            queryset = self.task_service.get_overdue_tasks()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = TaskReadSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = TaskReadSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def high_priority(self, request):
        """Задачи с высоким приоритетом."""
        try:
            queryset = self.task_service.get_high_priority_tasks()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = TaskReadSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = TaskReadSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='get',
        operation_description="Получить статистику задач пользователя",
        operation_summary="Статистика задач",
        responses={
            200: openapi.Response(
                'Статистика задач',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total': openapi.Schema(type=openapi.TYPE_INTEGER, description='Всего задач'),
                        'completed': openapi.Schema(type=openapi.TYPE_INTEGER, description='Выполненных задач'),
                        'in_progress': openapi.Schema(type=openapi.TYPE_INTEGER, description='В процессе выполнения'),
                        'overdue': openapi.Schema(type=openapi.TYPE_INTEGER, description='Просроченных задач'),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика задач пользователя."""
        try:
            stats = self.task_service.get_task_statistics()
            return Response(stats)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_mark_done(self, request):
        """Массовое завершение задач."""
        task_ids = request.data.get('task_ids', [])
        if not task_ids:
            return Response(
                {'error': 'Необходимо указать task_ids'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            completed_tasks = self.task_service.bulk_mark_done(task_ids)
            serializer = TaskReadSerializer(completed_tasks, many=True)
            return Response({
                'completed_count': len(completed_tasks),
                'tasks': serializer.data
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """Массовое обновление статуса задач."""
        task_ids = request.data.get('task_ids', [])
        new_status = request.data.get('status')
        
        if not task_ids or not new_status:
            return Response(
                {'error': 'Необходимы task_ids и status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            updated_tasks = self.task_service.bulk_update_status(task_ids, new_status)
            serializer = TaskReadSerializer(updated_tasks, many=True)
            return Response({
                'updated_count': len(updated_tasks),
                'tasks': serializer.data
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
