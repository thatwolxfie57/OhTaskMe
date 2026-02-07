from rest_framework import serializers
from .models import Event
from tasks.models import Task

class TaskInEventSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying tasks within an event.
    """
    class Meta:
        model = Task
        fields = ['id', 'description', 'scheduled_time', 'completed']
        read_only_fields = ['id', 'completed']

class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for Event model.
    """
    tasks = TaskInEventSerializer(many=True, read_only=True)
    owner = serializers.ReadOnlyField(source='owner.username')
    duration_minutes = serializers.ReadOnlyField(source='duration')
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'start_time', 'end_time', 
            'location', 'created_at', 'updated_at', 'owner', 
            'tasks', 'duration_minutes'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

class EventCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating an event.
    """
    id = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'start_time', 'end_time', 'location']
        read_only_fields = ['id']
        
    def validate(self, data):
        """
        Validate that end_time is after start_time.
        """
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("End time must be after start time")
        return data

class EventUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an event.
    """
    id = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'start_time', 'end_time', 'location']
        read_only_fields = ['id']
        
    def validate(self, data):
        """
        Validate that end_time is after start_time if both are present.
        """
        # If we're updating both start and end time
        if 'start_time' in data and 'end_time' in data:
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError("End time must be after start time")
        
        # If we're only updating end_time
        elif 'end_time' in data and 'start_time' not in data:
            if data['end_time'] <= self.instance.start_time:
                raise serializers.ValidationError("End time must be after start time")
        
        # If we're only updating start_time
        elif 'start_time' in data and 'end_time' not in data:
            if self.instance.end_time <= data['start_time']:
                raise serializers.ValidationError("End time must be after start time")
                
        return data
