from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Event model.
    """
    list_display = ('title', 'start_time', 'end_time', 'owner', 'duration')
    list_filter = ('start_time', 'end_time', 'owner')
    search_fields = ('title', 'description', 'location')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_time'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'location')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Ownership', {
            'fields': ('owner',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration(self, obj):
        """
        Display the duration of the event in hours and minutes.
        """
        minutes = obj.duration
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if hours > 0:
            return f"{hours} hr{'s' if hours != 1 else ''} {remaining_minutes} min{'s' if remaining_minutes != 1 else ''}"
        return f"{minutes} min{'s' if minutes != 1 else ''}"
    
    duration.short_description = 'Duration'
