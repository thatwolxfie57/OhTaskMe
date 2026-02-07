from rest_framework import serializers
from django.utils import timezone
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    """
    Default serializer for Task model.
    
    This serializer handles Task creation, listing, and retrieval. It automatically
    assigns the current user as the owner when creating tasks.
    
    Fields:
        id (int): The unique identifier for the task.
        description (str): A brief description of the task.
        scheduled_time (datetime): When the task is scheduled to be performed.
        created_at (datetime): When the task was created (read-only).
        updated_at (datetime): When the task was last updated (read-only).
        completed (bool): Whether the task has been completed.
        completed_at (datetime): When the task was completed (read-only).
        event (int): The ID of the associated event, if any.
    """
    class Meta:
        model = Task
        fields = ['id', 'description', 'scheduled_time', 'created_at', 
                  'updated_at', 'completed', 'completed_at', 'event']
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    
    def create(self, validated_data):
        """
        Create a new task for the current user.
        """
        # Get the current user from the context
        user = self.context['request'].user
        # Create the task with the user as owner
        task = Task.objects.create(owner=user, **validated_data)
        return task

class TaskDetailSerializer(TaskSerializer):
    """
    Extended serializer for detailed Task information.
    
    This serializer extends the base TaskSerializer to include owner information
    when retrieving detailed task information. It's used for GET operations
    on individual tasks.
    
    Additional Fields:
        owner (int): The ID of the user who owns the task.
    """
    
    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['owner']
        read_only_fields = TaskSerializer.Meta.read_only_fields + ['owner']

class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a Task.
    
    This serializer allows updating specific fields of a Task. It also handles
    the completion status changes automatically - if a task is marked as completed,
    it sets the completed_at timestamp, and if marked as incomplete, it clears
    the timestamp.
    
    Fields:
        description (str): A brief description of the task.
        scheduled_time (datetime): When the task is scheduled to be performed.
        completed (bool): Whether the task has been completed.
        event (int): The ID of the associated event, if any.
    """
    class Meta:
        model = Task
        fields = ['description', 'scheduled_time', 'completed', 'event']
    
    def update(self, instance, validated_data):
        """
        Update a task and handle completion status changes.
        """
        was_completed = instance.completed
        is_completed = validated_data.get('completed', was_completed)
        
        # Call the parent update method
        instance = super().update(instance, validated_data)
        
        # Handle completion status change
        if is_completed and not was_completed:
            instance.completed_at = timezone.now()
            instance.save()
        elif not is_completed and was_completed:
            instance.completed_at = None
            instance.save()
            
        return instance
