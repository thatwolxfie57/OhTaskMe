from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User

class CustomUserAdmin(UserAdmin):
    """
    Custom admin interface for the User model.
    
    Extends the built-in UserAdmin and adds the timezone field to the appropriate fieldsets.
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Preferences'), {'fields': ('timezone',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'timezone'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'timezone', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

admin.site.register(User, CustomUserAdmin)
