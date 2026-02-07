import django_filters
from django.utils import timezone
from .models import Task

class TaskFilter(django_filters.FilterSet):
    """
    FilterSet for Task model.
    
    Provides custom filtering options for the Task API:
    
    - start_date: Filter tasks with scheduled_time on or after this date
    - end_date: Filter tasks with scheduled_time on or before this date
    - completed: Filter tasks by completion status (true/false)
    
    Example usage:
    
    - Filter tasks scheduled after 2025-01-01: ?start_date=2025-01-01
    - Filter tasks scheduled before 2025-12-31: ?end_date=2025-12-31
    - Filter completed tasks: ?completed=true
    - Filter tasks in a date range: ?start_date=2025-01-01&end_date=2025-12-31
    - Filter incomplete tasks in a date range: ?start_date=2025-01-01&end_date=2025-12-31&completed=false
    """
    start_date = django_filters.DateFilter(field_name='scheduled_time', lookup_expr='date__gte')
    end_date = django_filters.DateFilter(field_name='scheduled_time', lookup_expr='date__lte')
    completed = django_filters.BooleanFilter(field_name='completed')
    
    class Meta:
        model = Task
        fields = ['start_date', 'end_date', 'completed']
