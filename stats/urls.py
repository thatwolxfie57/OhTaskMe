from django.urls import path
from . import views
from .debug_views import debug_chart_data

app_name = 'stats'

urlpatterns = [
    # Main dashboard
    path('', views.statistics_dashboard, name='dashboard'),
    
    # Debug endpoint
    path('debug/chart-data/', debug_chart_data, name='debug_chart_data'),
    
    # Achievement system
    path('achievements/', views.achievements_gallery, name='achievements'),
    
    # Goals management
    path('goals/', views.goals_management, name='goals_management'),
    path('goals/<int:goal_id>/update/', views.update_goal_progress, name='update_goal_progress'),
    
    # Streaks tracking
    path('streaks/', views.streaks_tracking, name='streaks'),
    path('streaks/create/', views.create_streak, name='create_streak'),
    path('streaks/<int:streak_id>/increment/', views.increment_streak, name='increment_streak'),
    path('streaks/<int:streak_id>/pause/', views.pause_streak, name='pause_streak'),
    path('streaks/<int:streak_id>/reactivate/', views.reactivate_streak, name='reactivate_streak'),
    
    # Productivity insights
    path('insights/', views.productivity_insights, name='insights'),
    
    # Mood tracking
    path('mood/', views.daily_mood_tracking, name='mood_tracking'),
    
    # API endpoints
    path('api/data/', views.statistics_api, name='api_data'),
    path('api/dashboard/', views.dashboard_api, name='api_dashboard'),
]
