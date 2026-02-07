from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Event
from .serializers import EventSerializer, EventCreateSerializer, EventUpdateSerializer
from tasks.models import Task
from tasks.serializers import TaskSerializer
from .task_suggestions import generate_task_suggestions, get_feedback_for_suggestions
from .task_suggestion_serializers import TaskSuggestionSerializer
from .training_pipeline import update_model_with_feedback

class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Events.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['start_time', 'end_time']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_time', 'end_time', 'created_at', 'title']
    ordering = ['start_time']
    
    def get_queryset(self):
        """
        This view returns a list of all events owned by the requesting user.
        """
        # Check if this is a schema request (for Swagger/OpenAPI documentation)
        if getattr(self, 'swagger_fake_view', False):
            return Event.objects.none()
            
        return Event.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the request method.
        """
        if self.action == 'create':
            return EventCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EventUpdateSerializer
        return EventSerializer
    
    def perform_create(self, serializer):
        """
        Set the owner of the event to the requesting user.
        """
        serializer.save(owner=self.request.user)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Get Event Tasks",
        operation_description="Return a list of tasks associated with this event.",
        responses={
            200: openapi.Response(
                description="List of tasks for the event",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            ),
            404: openapi.Response(description="Event not found")
        }
    )
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """
        Return a list of tasks associated with this event.
        """
        event = self.get_object()
        tasks = Task.objects.filter(event=event)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Add Task to Event",
        operation_description="Add an existing task to this event.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['task_id'],
            properties={
                'task_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID of the task to add to the event'
                )
            }
        ),
        responses={
            200: openapi.Response(description="Task successfully added to event"),
            404: openapi.Response(description="Task or event not found"),
            400: openapi.Response(description="Invalid request data")
        }
    )
    @action(detail=True, methods=['post'])
    def add_task(self, request, pk=None):
        """
        Add an existing task to this event.
        """
        event = self.get_object()
        try:
            task_id = request.data.get('task_id')
            task = Task.objects.get(id=task_id, owner=request.user)
            task.event = event
            task.save()
            return Response({'status': 'task added to event'}, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Remove Task from Event",
        operation_description="Remove a task from this event.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['task_id'],
            properties={
                'task_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID of the task to remove from the event'
                )
            }
        ),
        responses={
            200: openapi.Response(description="Task successfully removed from event"),
            404: openapi.Response(description="Task not found in this event"),
            400: openapi.Response(description="Invalid request data")
        }
    )
    @action(detail=True, methods=['post'])
    def remove_task(self, request, pk=None):
        """
        Remove a task from this event.
        """
        event = self.get_object()
        try:
            task_id = request.data.get('task_id')
            task = Task.objects.get(id=task_id, owner=request.user, event=event)
            task.event = None
            task.save()
            return Response({'status': 'task removed from event'}, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found in this event'}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Generate Preparation Tasks",
        operation_description="Generate preparation tasks for the event using AI.",
        responses={
            201: openapi.Response(
                description="Tasks generated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            ),
            404: openapi.Response(description="Event not found")
        }
    )
    @action(detail=True, methods=['post'])
    def generate_tasks(self, request, pk=None):
        """
        Generate preparation tasks for the event.
        """
        event = self.get_object()
        tasks = event.generate_preparation_tasks()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def distribute_tasks(self, request, pk=None):
        """
        Distribute tasks evenly based on schedule.
        """
        event = self.get_object()
        task_descriptions = request.data.get('task_descriptions', [])
        
        if not task_descriptions:
            return Response(
                {'error': 'No task descriptions provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = event.distribute_work_based_on_schedule(task_descriptions)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Get Event Workload Analysis",
        operation_description="Check workload for days around the event.",
        manual_parameters=[
            openapi.Parameter(
                'days_before',
                openapi.IN_QUERY,
                description="Number of days before event to analyze",
                type=openapi.TYPE_INTEGER,
                default=7
            ),
            openapi.Parameter(
                'days_after',
                openapi.IN_QUERY,
                description="Number of days after event to analyze",
                type=openapi.TYPE_INTEGER,
                default=7
            ),
        ],
        responses={
            200: openapi.Response(
                description="Workload analysis data",
                examples={
                    "application/json": {
                        "2024-01-01": 3,
                        "2024-01-02": 5,
                        "2024-01-03": 2
                    }
                }
            )
        }
    )
    @action(detail=True, methods=['get'])
    def workload(self, request, pk=None):
        """
        Check workload for days around the event.
        """
        event = self.get_object()
        days_before = int(request.query_params.get('days_before', 7))
        days_after = int(request.query_params.get('days_after', 7))
        
        start_date = event.start_time.date() - datetime.timedelta(days=days_before)
        end_date = event.end_time.date() + datetime.timedelta(days=days_after)
        
        workload = {}
        current_date = start_date
        
        while current_date <= end_date:
            workload[str(current_date)] = event.check_workload_for_day(current_date)['count']
            current_date += datetime.timedelta(days=1)
        
        return Response(workload)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Return a list of upcoming events.
        """
        upcoming_events = Event.objects.filter(
            owner=request.user,
            start_time__gt=timezone.now()
        ).order_by('start_time')
        
        serializer = self.get_serializer(upcoming_events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        """
        Return a list of past events.
        """
        past_events = Event.objects.filter(
            owner=request.user,
            end_time__lt=timezone.now()
        ).order_by('-end_time')
        
        serializer = self.get_serializer(past_events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Return a list of today's events.
        """
        now = timezone.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        today_events = Event.objects.filter(
            owner=request.user
        ).filter(
            Q(start_time__range=(start_of_day, end_of_day)) | 
            Q(end_time__range=(start_of_day, end_of_day)) |
            Q(start_time__lt=start_of_day, end_time__gt=end_of_day)
        ).order_by('start_time')
        
        serializer = self.get_serializer(today_events, many=True)
        return Response(serializer.data)
        
    @swagger_auto_schema(
        method='get',
        operation_summary="Get AI Task Suggestions",
        operation_description="""
        Get AI-generated task suggestions for the event.
        
        Uses advanced NLP and ML techniques to analyze the event title and description,
        and generates relevant task suggestions with confidence scores.
        
        Features:
        - Event type classification (meeting, conference, travel, workshop, etc.)
        - Keyword extraction using spaCy NLP
        - Complexity analysis based on event duration and content
        - Confidence scoring (0-95%) for each suggestion
        - Context-aware task timing and scheduling
        """,
        responses={
            200: openapi.Response(
                description="AI-generated task suggestions",
                examples={
                    "application/json": [
                        {
                            "description": "Prepare presentation slides for Team Meeting",
                            "scheduled_time": "2024-01-15T10:00:00Z",
                            "confidence": 85,
                            "category": "meeting",
                            "relation": "before",
                            "analysis_notes": "Based on meeting pattern with medium complexity"
                        }
                    ]
                }
            ),
            404: openapi.Response(description="Event not found")
        }
    )
    @action(detail=True, methods=['get'])
    def suggest_tasks(self, request, pk=None):
        """
        Get AI-generated task suggestions for the event.
        
        Uses NLP and ML techniques to analyze the event title and description,
        and generates relevant task suggestions with confidence scores.
        
        Returns:
            A list of task suggestions with descriptions, scheduled times, and confidence scores.
        """
        event = self.get_object()
        suggestions = generate_task_suggestions(event)
        
        # Use the serializer to format the response
        serializer = TaskSuggestionSerializer(suggestions, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Create Tasks from AI Suggestions",
        operation_description="""
        Create tasks from the selected AI suggestions and process feedback.
        
        This endpoint creates actual Task objects from selected suggestions
        and processes user feedback to improve future AI recommendations
        through the machine learning training pipeline.
        
        Features:
        - Creates tasks with proper scheduling and event association
        - Processes user feedback for machine learning improvement
        - Updates AI model weights based on acceptance/rejection patterns
        - Provides analytics data for suggestion quality assessment
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['selected_suggestions'],
            properties={
                'selected_suggestions': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                    description='List of suggestion objects to create tasks from'
                ),
                'rejected_suggestions': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                    description='List of suggestion objects that were rejected'
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Tasks created successfully and feedback processed",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            ),
            400: openapi.Response(description="No suggestions selected or invalid data"),
            404: openapi.Response(description="Event not found")
        }
    )
    @action(detail=True, methods=['post'])
    def create_suggested_tasks(self, request, pk=None):
        """
        Create tasks from the selected suggestions.
        
        Takes a list of selected and rejected suggestions and creates tasks
        for the selected ones. Also processes the feedback to improve
        future AI suggestions through the training pipeline.
        
        Request Body:
            selected_suggestions: List of suggestion objects to create tasks from
            rejected_suggestions: List of suggestion objects that were rejected
            
        Returns:
            A list of the created tasks with their details.
        """
        event = self.get_object()
        selected_suggestions = request.data.get('selected_suggestions', [])
        rejected_suggestions = request.data.get('rejected_suggestions', [])
        
        if not selected_suggestions:
            return Response(
                {'error': 'No suggestions selected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_tasks = []
        
        # Create tasks for each selected suggestion
        for suggestion in selected_suggestions:
            task = Task.objects.create(
                description=suggestion['description'],
                scheduled_time=suggestion['scheduled_time'],
                owner=request.user,
                event=event,
                completed=False
            )
            created_tasks.append(task)
        
        # Process feedback to improve future suggestions
        get_feedback_for_suggestions(selected_suggestions, rejected_suggestions, event)
        
        # Update ML model with feedback
        try:
            update_model_with_feedback(selected_suggestions, rejected_suggestions, event)
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error updating model with feedback: {str(e)}")
        
        # Return the created tasks
        serializer = TaskSerializer(created_tasks, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
