from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Task(models.Model):
    """
    Represents a task in the OhTaskMe application.
    
    A task is an activity that needs to be completed by a user, optionally
    associated with an event. Each task has a description, scheduled time,
    and completion status.
    
    Attributes:
        description (str): A brief description of the task.
        scheduled_time (datetime): The date and time when the task is scheduled.
        created_at (datetime): The date and time when the task was created (auto-set).
        updated_at (datetime): The date and time when the task was last updated (auto-updated).
        completed (bool): Indicates whether the task has been completed.
        completed_at (datetime): The date and time when the task was completed (if completed).
        owner (User): The user who owns this task.
        event (Event): The event this task is associated with (optional).
    """
    description = models.CharField(
        _('description'),
        max_length=255,
        help_text=_('A brief description of the task.')
    )
    
    scheduled_time = models.DateTimeField(
        _('scheduled time'),
        help_text=_('The date and time when the task is scheduled.')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('The date and time when the task was created.')
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('The date and time when the task was last updated.')
    )
    
    completed = models.BooleanField(
        _('completed'),
        default=False,
        help_text=_('Indicates whether the task has been completed.')
    )
    
    completed_at = models.DateTimeField(
        _('completed at'),
        null=True, 
        blank=True,
        help_text=_('The date and time when the task was completed.')
    )
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text=_('The user who owns this task.')
    )
    
    # This field is set to the event if this task is associated with an event
    event = models.ForeignKey(
        'events.Event', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text=_('The event this task is associated with.')
    )
    
    class Meta:
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        ordering = ['scheduled_time']
    
    def __str__(self):
        """
        Returns a string representation of the task.
        """
        return f"{self.description} at {self.scheduled_time}"
    
    def mark_as_completed(self):
        """
        Marks the task as completed and sets the completion time.
        """
        from django.utils import timezone
        self.completed = True
        self.completed_at = timezone.now()
        self.save()
        
    def mark_as_incomplete(self):
        """
        Marks the task as incomplete and resets the completion time.
        """
        self.completed = False
        self.completed_at = None
        self.save()
