from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime

User = get_user_model()

class Event(models.Model):
    """
    Event model for organizing tasks and planning events.
    
    TODO: Add user preference integration for personalized event handling
    TODO: Implement event complexity scoring and automatic categorization
    TODO: Add relationship to user profile for context-aware task generation
    TODO: Implement machine learning features for predictive task suggestions
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    
    class Meta:
        ordering = ['start_time']
        
    def __str__(self):
        return self.title
        
    @property
    def duration(self):
        """
        Return the duration of the event in minutes.
        """
        return (self.end_time - self.start_time).total_seconds() // 60
        
    def is_upcoming(self):
        """
        Check if the event is upcoming.
        """
        return self.start_time > timezone.now()
        
    def is_ongoing(self):
        """
        Check if the event is currently ongoing.
        """
        now = timezone.now()
        return self.start_time <= now <= self.end_time
        
    @property
    def is_past(self):
        """
        Check if the event is in the past.
        """
        return self.end_time < timezone.now()
        
    def get_tasks(self):
        """
        Get all tasks associated with this event.
        """
        return self.tasks.all()
    
    def generate_preparation_tasks(self):
        """
        Generate preparation tasks for this event.
        
        Creates three tasks:
        1. Preparation task 3 days before event
        2. Final check task 1 day before event
        3. Follow-up task 1 day after event
        
        Returns the created tasks.
        """
        from tasks.models import Task
        
        # Calculate task times
        prep_time = self.start_time - datetime.timedelta(days=3)
        check_time = self.start_time - datetime.timedelta(days=1)
        followup_time = self.end_time + datetime.timedelta(days=1)
        
        # Create the tasks
        tasks = []
        
        prep_task = Task.objects.create(
            description=f"Prepare for: {self.title}",
            scheduled_time=prep_time,
            owner=self.owner,
            event=self
        )
        tasks.append(prep_task)
        
        check_task = Task.objects.create(
            description=f"Final check for: {self.title}",
            scheduled_time=check_time,
            owner=self.owner,
            event=self
        )
        tasks.append(check_task)
        
        followup_task = Task.objects.create(
            description=f"Follow up after: {self.title}",
            scheduled_time=followup_time,
            owner=self.owner,
            event=self
        )
        tasks.append(followup_task)
        
        return tasks
    
    def distribute_work_based_on_schedule(self, task_descriptions):
        """
        Distribute tasks evenly based on user's schedule.
        
        Args:
            task_descriptions: List of task descriptions to create
            
        Returns:
            List of created tasks
        """
        from tasks.models import Task
        
        # Get all existing tasks for this user during the event period
        start_date = self.start_time.date() - datetime.timedelta(days=7)
        end_date = self.end_time.date() + datetime.timedelta(days=7)
        
        user_tasks = Task.objects.filter(
            owner=self.owner, 
            scheduled_time__date__range=(start_date, end_date)
        ).order_by('scheduled_time')
        
        # Count tasks per day
        task_counts = {}
        for task in user_tasks:
            day = task.scheduled_time.date()
            if day in task_counts:
                task_counts[day] += 1
            else:
                task_counts[day] = 1
        
        # Determine available days (with fewer tasks)
        available_days = []
        current_date = start_date
        while current_date <= end_date:
            # Prefer days with fewer tasks
            count = task_counts.get(current_date, 0)
            available_days.append((current_date, count))
            current_date += datetime.timedelta(days=1)
        
        # Sort by task count
        available_days.sort(key=lambda x: x[1])
        
        # Distribute tasks
        created_tasks = []
        for i, description in enumerate(task_descriptions):
            # Get the day with the fewest tasks
            day, _ = available_days[i % len(available_days)]
            
            # Create task at 10 AM on that day
            task_time = datetime.datetime.combine(
                day, 
                datetime.time(10, 0),
                tzinfo=timezone.get_current_timezone()
            )
            
            task = Task.objects.create(
                description=description,
                scheduled_time=task_time,
                owner=self.owner,
                event=self
            )
            created_tasks.append(task)
            
            # Update task count for this day
            for j, (d, count) in enumerate(available_days):
                if d == day:
                    available_days[j] = (d, count + 1)
                    break
            
            # Re-sort by task count
            available_days.sort(key=lambda x: x[1])
        
        return created_tasks
    
    def check_workload_for_day(self, date):
        """
        Check the workload for a specific day.
        
        Args:
            date: The date to check
            
        Returns:
            Dictionary with task count and list of tasks
        """
        from tasks.models import Task
        
        day_start = datetime.datetime.combine(date, datetime.time.min, tzinfo=timezone.get_current_timezone())
        day_end = datetime.datetime.combine(date, datetime.time.max, tzinfo=timezone.get_current_timezone())
        
        tasks = Task.objects.filter(
            owner=self.owner,
            scheduled_time__range=(day_start, day_end)
        )
        
        return {
            'count': tasks.count(),
            'tasks': list(tasks)
        }
    
    def suggest_tasks(self):
        """
        Generate AI-based task suggestions for this event.
        
        This method integrates with the task_suggestions module to create
        intelligent task suggestions based on event details and NLP analysis.
        
        Returns:
            List of task suggestions
        """
        from .task_suggestions import generate_task_suggestions
        
        # Generate task suggestions
        suggestions = generate_task_suggestions(self)
        
        return suggestions
