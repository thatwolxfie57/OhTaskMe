"""
Serializers for the task suggestions module.
"""
from rest_framework import serializers
import uuid

class TaskSuggestionSerializer(serializers.Serializer):
    """
    Serializer for task suggestions.
    
    Fields:
        id: Unique identifier for the suggestion
        description: The suggested task description
        scheduled_time: Recommended time to schedule the task
        confidence: AI confidence score (0-1) for the suggestion
        relation: Whether the task is 'before' or 'after' the event
    """
    id = serializers.CharField(default=str)
    description = serializers.CharField()
    scheduled_time = serializers.DateTimeField()
    confidence = serializers.FloatField()
    relation = serializers.CharField()
    
    class Meta:
        fields = ['id', 'description', 'scheduled_time', 'confidence', 'relation']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If id isn't set, generate a unique ID
        if args and isinstance(args[0], dict) and 'id' not in args[0]:
            args[0]['id'] = str(uuid.uuid4())
