from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('password-change/', views.password_change, name='password_change'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Task URLs
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:task_id>/toggle/', views.task_toggle, name='task_toggle'),
    path('tasks/calendar/', views.task_calendar, name='task_calendar'),
    path('tasks/ajax/toggle/', views.ajax_task_toggle, name='ajax_task_toggle'),
    
    # Event URLs
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/edit/', views.event_edit, name='event_edit'),
    path('events/<int:event_id>/delete/', views.event_delete, name='event_delete'),
    path('events/calendar/', views.event_calendar, name='event_calendar'),
    path('events/<int:event_id>/generate-tasks/', views.generate_event_tasks, name='generate_event_tasks'),
    path('events/<int:event_id>/suggest-tasks/', views.suggest_event_tasks, name='suggest_event_tasks'),
    path('events/<int:event_id>/create-suggested-tasks/', views.create_suggested_tasks, name='create_suggested_tasks'),
    
    # Integrated Calendar URLs
    path('calendar/', views.integrated_calendar, name='integrated_calendar'),
    
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
]
