"""
API URLs for OhTaskMe JavaScript enhancements
"""

from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    # Real-time updates
    path('task-updates/', api_views.TaskUpdatesView.as_view(), name='task_updates'),
    
    # Task management
    path('tasks/move/', api_views.move_task, name='move_task'),
    path('tasks/quick-create/', api_views.quick_create_task, name='quick_create_task'),
    
    # Conflict detection
    path('conflicts/', api_views.check_conflicts, name='check_conflicts'),
    
    # Statistics
    path('stats/latest/', api_views.stats_latest, name='stats_latest'),
    path('stats/task-completion/', api_views.task_completion_stats, name='task_completion_stats'),
    path('stats/weekly-activity/', api_views.weekly_activity_stats, name='weekly_activity_stats'),
    path('stats/time-distribution/', api_views.time_distribution_stats, name='time_distribution_stats'),
    
    # Event statistics
    path('event-stats/', api_views.event_stats, name='event_stats'),
]
