from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Task model.
    """
    list_display = ('description', 'scheduled_time', 'owner', 'completed', 'created_at')
    list_filter = ('completed', 'created_at', 'scheduled_time')
    search_fields = ('description', 'owner__username')
    date_hierarchy = 'scheduled_time'
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    fieldsets = (
        (None, {
            'fields': ('description', 'scheduled_time', 'owner')
        }),
        ('Status', {
            'fields': ('completed', 'completed_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
