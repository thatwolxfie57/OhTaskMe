from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Task
from .serializers import TaskSerializer, TaskDetailSerializer, TaskUpdateSerializer
from .filters import TaskFilter

class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing tasks.
    
    Provides full CRUD operations for Task instances:
    * List all tasks for the authenticated user
    * Create a new task
    * Retrieve a specific task
    * Update a task
    * Delete a task
    
    Additional actions:
    * Mark a task as complete
    * Mark a task as incomplete
    * List today's tasks
    * List upcoming tasks
    * List overdue tasks
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['description']
    ordering_fields = ['scheduled_time', 'created_at', 'updated_at']
    ordering = ['scheduled_time']
    
    # Add a tag for all actions in this viewset
    swagger_tags = ['tasks']

    def get_queryset(self):
        """
        Return tasks for the current authenticated user only.
        """
        # Handle the case when this is called during schema generation
        if getattr(self, 'swagger_fake_view', False):
            # Return an empty queryset
            return Task.objects.none()
            
        return Task.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'retrieve':
            return TaskDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskSerializer
    
    @swagger_auto_schema(
        operation_description="List all tasks for the authenticated user.",
        operation_id="tasks_list",
        responses={
            200: TaskSerializer(many=True),
            401: "Authentication credentials were not provided."
        },
        manual_parameters=[
            openapi.Parameter(
                'start_date', 
                openapi.IN_QUERY, 
                description="Filter tasks with scheduled_time on or after this date (YYYY-MM-DD)", 
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'end_date', 
                openapi.IN_QUERY, 
                description="Filter tasks with scheduled_time on or before this date (YYYY-MM-DD)", 
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'completed', 
                openapi.IN_QUERY, 
                description="Filter tasks by completion status (true/false)", 
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'search', 
                openapi.IN_QUERY, 
                description="Search tasks by description", 
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'ordering', 
                openapi.IN_QUERY, 
                description="Order tasks by field (e.g. scheduled_time, -scheduled_time for descending)", 
                type=openapi.TYPE_STRING
            )
        ],
        examples={
            "application/json": {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "description": "Complete project report",
                        "scheduled_time": "2025-08-15T15:30:00Z",
                        "created_at": "2025-08-01T12:00:00Z",
                        "updated_at": "2025-08-01T12:00:00Z",
                        "completed": False,
                        "completed_at": None,
                        "event": None
                    },
                    {
                        "id": 2,
                        "description": "Team meeting preparation",
                        "scheduled_time": "2025-08-16T09:00:00Z",
                        "created_at": "2025-08-02T10:00:00Z",
                        "updated_at": "2025-08-02T10:00:00Z",
                        "completed": True,
                        "completed_at": "2025-08-03T15:45:00Z",
                        "event": 1
                    }
                ]
            }
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new task.",
        operation_id="tasks_create",
        request_body=TaskSerializer,
        responses={
            201: TaskSerializer,
            400: "Invalid request data",
            401: "Authentication credentials were not provided."
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Retrieve a specific task.",
        operation_id="tasks_read",
        responses={
            200: TaskDetailSerializer,
            401: "Authentication credentials were not provided.",
            404: "Not found."
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
        
    @swagger_auto_schema(
        operation_description="Update a task (partial update supported).",
        operation_id="tasks_partial_update",
        request_body=TaskUpdateSerializer,
        responses={
            200: TaskDetailSerializer,
            400: "Invalid request data",
            401: "Authentication credentials were not provided.",
            404: "Not found."
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        operation_description="Mark a task as completed.",
        operation_id="tasks_complete",
        responses={
            200: TaskDetailSerializer,
            401: "Authentication credentials were not provided.",
            404: "Not found."
        }
    )
    def complete(self, request, pk=None):
        """
        Mark a task as completed.
        
        Sets the completed flag to True and records the completion timestamp.
        """
        task = self.get_object()
        task.mark_as_completed()
        return Response(TaskDetailSerializer(task).data)
    
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        operation_description="Mark a task as incomplete.",
        operation_id="tasks_incomplete",
        responses={
            200: TaskDetailSerializer,
            401: "Authentication credentials were not provided.",
            404: "Not found."
        }
    )
    def incomplete(self, request, pk=None):
        """
        Mark a task as incomplete.
        
        Sets the completed flag to False and clears the completion timestamp.
        """
        task = self.get_object()
        task.mark_as_incomplete()
        return Response(TaskDetailSerializer(task).data)
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_description="List all tasks scheduled for today.",
        operation_id="tasks_today",
        responses={
            200: TaskSerializer(many=True),
            401: "Authentication credentials were not provided."
        },
        manual_parameters=[
            openapi.Parameter(
                'page', 
                openapi.IN_QUERY, 
                description="Page number for pagination", 
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', 
                openapi.IN_QUERY, 
                description="Number of items per page", 
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def today(self, request):
        """
        List all tasks scheduled for today.
        
        Returns all tasks belonging to the authenticated user that are scheduled
        for the current date, based on the user's timezone setting.
        """
        today = timezone.localtime().date()
        tasks = self.get_queryset().filter(
            scheduled_time__date=today
        )
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_description="List all upcoming tasks (scheduled for the future).",
        responses={200: TaskSerializer(many=True)}
    )
    def upcoming(self, request):
        """
        List all upcoming tasks (scheduled for the future).
        """
        now = timezone.now()
        tasks = self.get_queryset().filter(
            scheduled_time__gt=now
        )
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_description="List all overdue tasks (past scheduled time and not completed).",
        responses={200: TaskSerializer(many=True)}
    )
    def overdue(self, request):
        """
        List all overdue tasks (past scheduled time and not completed).
        """
        now = timezone.now()
        tasks = self.get_queryset().filter(
            scheduled_time__lt=now,
            completed=False
        )
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
