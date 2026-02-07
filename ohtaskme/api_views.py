"""
API Views for OhTaskMe
Provides AJAX endpoints for JavaScript enhancements
"""

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import time
from typing import Dict, Any

from tasks.models import Task
from events.models import Event


class TaskUpdatesView(View):
    """
    Server-Sent Events endpoint for real-time task updates
    """
    
    def get(self, request):
        """
        Stream real-time updates using Server-Sent Events
        """
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        def event_stream():
            """Generator for streaming events"""
            while True:
                # Get recent task updates for the user
                recent_tasks = Task.objects.filter(
                    owner=request.user,
                    updated_at__gte=timezone.now() - timedelta(minutes=5)
                ).order_by('-updated_at')[:5]
                
                if recent_tasks:
                    data = {
                        'type': 'task_update',
                        'tasks': [
                            {
                                'id': task.id,
                                'description': task.description,
                                'completed': task.completed,
                                'scheduled_time': task.scheduled_time.isoformat() if task.scheduled_time else None,
                                'updated_at': task.updated_at.isoformat()
                            }
                            for task in recent_tasks
                        ],
                        'timestamp': timezone.now().isoformat()
                    }
                    
                    yield f"data: {json.dumps(data, cls=DjangoJSONEncoder)}\n\n"
                
                time.sleep(5)  # Wait 5 seconds before next check
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        # Remove Connection header to avoid hop-by-hop header error
        response['Access-Control-Allow-Origin'] = '*'
        return response


@csrf_exempt
@require_http_methods(["POST"])
def move_task(request):
    """
    Move a task to a new date/time
    """
    # Check authentication for AJAX requests
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in to move tasks.'}, status=401)
    
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_date = data.get('new_date')
        new_time = data.get('new_time', '09:00')
        
        if not task_id or not new_date:
            return JsonResponse({'error': 'task_id and new_date are required'}, status=400)
        
        # Get the task
        try:
            task = Task.objects.get(id=task_id, owner=request.user)
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)
        
        # Parse the new datetime
        try:
            if isinstance(new_date, str):
                if 'T' in new_date:
                    # Full datetime string
                    new_datetime = datetime.fromisoformat(new_date.replace('Z', '+00:00'))
                else:
                    # Just date, combine with time
                    date_part = datetime.strptime(new_date, '%Y-%m-%d').date()
                    time_part = datetime.strptime(new_time, '%H:%M').time()
                    new_datetime = datetime.combine(date_part, time_part)
                
                # Make timezone aware
                if timezone.is_naive(new_datetime):
                    new_datetime = timezone.make_aware(new_datetime)
                
                task.scheduled_time = new_datetime
                task.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Task moved successfully',
                    'task': {
                        'id': task.id,
                        'description': task.description,
                        'scheduled_time': task.scheduled_time.isoformat(),
                        'completed': task.completed
                    }
                })
                
        except ValueError as e:
            return JsonResponse({'error': f'Invalid date format: {str(e)}'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def quick_create_task(request):
    """
    Quick task creation for calendar interactions
    """
    # Check authentication for AJAX requests
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    try:
        data = json.loads(request.body)
        description = data.get('description', '').strip()
        scheduled_time = data.get('scheduled_time')
        
        if not description:
            return JsonResponse({'error': 'Description is required'}, status=400)
        
        if not scheduled_time:
            return JsonResponse({'error': 'Scheduled time is required'}, status=400)
        
        # Parse scheduled time
        try:
            if isinstance(scheduled_time, str):
                scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                if timezone.is_naive(scheduled_datetime):
                    scheduled_datetime = timezone.make_aware(scheduled_datetime)
        except ValueError:
            return JsonResponse({'error': 'Invalid datetime format'}, status=400)
        
        # Create the task
        task = Task.objects.create(
            owner=request.user,
            description=description,
            scheduled_time=scheduled_datetime,
            completed=False
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Task created successfully',
            'task': {
                'id': task.id,
                'description': task.description,
                'scheduled_time': task.scheduled_time.isoformat(),
                'completed': task.completed,
                'created_at': task.created_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def check_conflicts(request):
    """
    Check for scheduling conflicts
    """
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    exclude_task = request.GET.get('exclude_task')
    exclude_event = request.GET.get('exclude_event')
    
    if not start_time:
        return JsonResponse({'error': 'start_time is required'}, status=400)
    
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            if timezone.is_naive(end_dt):
                end_dt = timezone.make_aware(end_dt)
        else:
            # Default to 1 hour duration
            end_dt = start_dt + timedelta(hours=1)
    
    except ValueError:
        return JsonResponse({'error': 'Invalid datetime format'}, status=400)
    
    conflicts = []
    
    # Check task conflicts
    task_conflicts = Task.objects.filter(
        owner=request.user,
        scheduled_time__range=[start_dt, end_dt],
        completed=False
    )
    
    if exclude_task:
        task_conflicts = task_conflicts.exclude(id=exclude_task)
    
    for task in task_conflicts:
        conflicts.append({
            'type': 'task',
            'id': task.id,
            'title': task.description,
            'time': task.scheduled_time.isoformat()
        })
    
    # Check event conflicts
    event_conflicts = Event.objects.filter(
        owner=request.user,
        start_time__lt=end_dt,
        end_time__gt=start_dt
    )
    
    if exclude_event:
        event_conflicts = event_conflicts.exclude(id=exclude_event)
    
    for event in event_conflicts:
        conflicts.append({
            'type': 'event',
            'id': event.id,
            'title': event.title,
            'start_time': event.start_time.isoformat(),
            'end_time': event.end_time.isoformat()
        })
    
    return JsonResponse({
        'conflicts': conflicts,
        'has_conflicts': len(conflicts) > 0,
        'message': f'Found {len(conflicts)} conflicts' if conflicts else 'No conflicts found'
    })


@login_required
def stats_latest(request):
    """
    Get latest statistics for dashboard updates
    """
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Task statistics
    total_tasks = Task.objects.filter(owner=request.user).count()
    completed_tasks = Task.objects.filter(owner=request.user, completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    
    today_tasks = Task.objects.filter(
        owner=request.user,
        scheduled_time__date=today
    ).count()
    
    today_completed = Task.objects.filter(
        owner=request.user,
        scheduled_time__date=today,
        completed=True
    ).count()
    
    # Weekly completion rate
    week_tasks = Task.objects.filter(
        owner=request.user,
        scheduled_time__date__gte=week_ago
    )
    week_completed = week_tasks.filter(completed=True).count()
    week_total = week_tasks.count()
    week_completion_rate = (week_completed / week_total * 100) if week_total > 0 else 0
    
    # Event statistics
    total_events = Event.objects.filter(owner=request.user).count()
    upcoming_events = Event.objects.filter(
        owner=request.user,
        start_time__gte=now
    ).count()
    
    return JsonResponse({
        'tasks': {
            'total': total_tasks,
            'completed': completed_tasks,
            'pending': pending_tasks,
            'today_total': today_tasks,
            'today_completed': today_completed,
            'week_completion_rate': round(week_completion_rate, 1)
        },
        'events': {
            'total': total_events,
            'upcoming': upcoming_events
        },
        'timestamp': now.isoformat(),
        'success': True
    })


@login_required
def task_completion_stats(request):
    """
    Get task completion statistics for charts
    """
    period = int(request.GET.get('period', 7))  # days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=period)
    
    tasks = Task.objects.filter(
        owner=request.user,
        scheduled_time__date__gte=start_date,
        scheduled_time__date__lte=end_date
    )
    
    completed = tasks.filter(completed=True).count()
    overdue = tasks.filter(
        completed=False,
        scheduled_time__lt=timezone.now()
    ).count()
    pending = tasks.filter(
        completed=False,
        scheduled_time__gte=timezone.now()
    ).count()
    
    return JsonResponse({
        'completed': completed,
        'pending': pending,
        'overdue': overdue,
        'total': completed + pending + overdue,
        'period': period
    })


@login_required
def weekly_activity_stats(request):
    """
    Get weekly activity statistics
    """
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    weekly_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        completed_count = Task.objects.filter(
            owner=request.user,
            scheduled_time__date=day,
            completed=True
        ).count()
        weekly_data.append(completed_count)
    
    return JsonResponse({
        'weekly_data': weekly_data,
        'week_start': week_start.isoformat(),
        'labels': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    })


@login_required
def time_distribution_stats(request):
    """
    Get time distribution statistics by hour
    """
    # Get tasks completed in the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    completed_tasks = Task.objects.filter(
        owner=request.user,
        completed=True,
        updated_at__gte=thirty_days_ago
    )
    
    # Initialize hourly data
    hourly_data = [0] * 24
    
    # Count tasks by hour of completion
    for task in completed_tasks:
        if task.updated_at:
            hour = task.updated_at.hour
            hourly_data[hour] += 1
    
    # Calculate insights
    peak_hour = hourly_data.index(max(hourly_data)) if max(hourly_data) > 0 else 0
    avg_tasks = sum(hourly_data) / 24 if sum(hourly_data) > 0 else 0
    
    # Find most productive period (3-hour window)
    max_productive = 0
    most_productive_start = 0
    for i in range(22):  # 0-21 to avoid index out of range
        window_sum = sum(hourly_data[i:i+3])
        if window_sum > max_productive:
            max_productive = window_sum
            most_productive_start = i
    
    total_completed = sum(hourly_data)
    total_scheduled = Task.objects.filter(
        owner=request.user,
        scheduled_time__gte=thirty_days_ago
    ).count()
    
    completion_rate = (total_completed / total_scheduled * 100) if total_scheduled > 0 else 0
    
    return JsonResponse({
        'hourly_data': hourly_data,
        'insights': {
            'peak_hour': f"{peak_hour:02d}:00",
            'avg_tasks': round(avg_tasks, 1),
            'most_productive': f"{most_productive_start:02d}:00-{most_productive_start+3:02d}:00",
            'completion_rate': round(completion_rate, 1)
        },
        'period_days': 30
    })


@login_required
def event_stats(request):
    """
    Get event statistics
    """
    now = timezone.now()
    
    total_events = Event.objects.filter(owner=request.user).count()
    upcoming_events = Event.objects.filter(
        owner=request.user,
        start_time__gte=now
    ).count()
    
    return JsonResponse({
        'total': total_events,
        'upcoming': upcoming_events
    })
