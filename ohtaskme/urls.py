"""
URL configuration for ohtaskme project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.authentication import SessionAuthentication
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

def debug_view(request):
    return HttpResponse("Debug view is working!")

def chrome_devtools_manifest(request):
    """Handle Chrome DevTools manifest request to prevent 404 errors"""
    return JsonResponse({}, status=204)  # Return empty JSON with 204 No Content

# Create a schema view for Swagger/OpenAPI documentation
schema_view = get_schema_view(
    openapi.Info(
        title="OhTaskMe API",
        default_version='v1',
        description="""
        API documentation for OhTaskMe - A comprehensive task and event management application with advanced statistics and gamification features.
        
        ## Core Features
        - **Task Management**: Create, update, delete, and track task completion
        - **Event Management**: Schedule and manage calendar events with integrated notifications
        - **User Management**: User authentication, profiles, and preferences
        - **Statistics & Gamification**: Comprehensive user analytics, XP system, achievements, and progress tracking
        
        ## Statistics System
        - **User Statistics**: Track XP, levels, task completion rates, and productivity scores
        - **Daily Statistics**: Monitor daily productivity metrics and trends
        - **Achievement System**: Earn badges and rewards for various milestones
        - **Streak Tracking**: Monitor consistent task completion patterns
        - **Goals Management**: Set and track personal productivity goals
        - **AI Insights**: Automated productivity analysis and recommendations
        
        ## Gamification Features
        - **XP & Leveling**: Gain experience points and level up
        - **Achievements**: Unlock various badges with different rarity levels
        - **Streaks**: Build and maintain productivity streaks
        - **Progress Tracking**: Visual progress indicators and analytics
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[SessionAuthentication],
    
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls', namespace='users')),
    path('api/tasks/', include('tasks.urls', namespace='tasks')),
    path('api/events/', include('events.urls', namespace='events')),
    
    # API endpoints for JavaScript enhancements
    path('api/', include('ohtaskme.api_urls', namespace='api')),
    
    # Debug URL
    path('debug/', debug_view, name='debug'),
    
    # Handle Chrome DevTools requests to prevent 404 errors
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools_manifest, name='chrome-devtools'),
    
    # Frontend URLs
    path('', include('ohtaskme.frontend_urls')),
    
    # Statistics and gamification URLs
    path('stats/', include('stats.urls', namespace='stats')),
    
    # Swagger documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
