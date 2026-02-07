from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
import datetime

from .models import Event
from tasks.models import Task

@receiver(post_save, sender=Event)
def generate_preparation_tasks(sender, instance, created, **kwargs):
    """
    Signal to automatically generate preparation tasks when an event is created.
    
    DISABLED: This signal has been disabled to give users control over task generation.
    Task generation is now handled through the UI in the event creation form.
    
    Generates the following tasks:
    1. Preparation task 3 days before event
    2. Final check task 1 day before event
    3. Follow-up task 1 day after event
    """
    # DISABLED: Automatic task generation is now handled through UI controls
    # Users can choose to generate tasks through the event creation form
    pass
    
    # OLD CODE (commented out):
    # if created:  # Only generate tasks when the event is first created
    #     # Generate preparation task (3 days before event)
    #     prep_time = instance.start_time - datetime.timedelta(days=3)
    #     Task.objects.create(
    #         description=f"Prepare for: {instance.title}",
    #         scheduled_time=prep_time,
    #         owner=instance.owner,
    #         event=instance
    #     )
    #     
    #     # Generate final check task (1 day before event)
    #     check_time = instance.start_time - datetime.timedelta(days=1)
    #     Task.objects.create(
    #         description=f"Final check for: {instance.title}",
    #         scheduled_time=check_time,
    #         owner=instance.owner,
    #         event=instance
    #     )
    #     
    #     # Generate follow-up task (1 day after event)
    #     followup_time = instance.end_time + datetime.timedelta(days=1)
    #     Task.objects.create(
    #         description=f"Follow up after: {instance.title}",
    #         scheduled_time=followup_time,
    #         owner=instance.owner,
    #         event=instance
    #     )

@receiver(post_delete, sender=Event)
def cleanup_event_tasks(sender, instance, **kwargs):
    """
    Signal to cleanup tasks when an event is deleted.
    
    Note: This may not be necessary with CASCADE delete behavior,
    but is included for robustness and in case of changes to the delete behavior.
    """
    # Find all tasks associated with this event
    Task.objects.filter(event=instance).delete()
