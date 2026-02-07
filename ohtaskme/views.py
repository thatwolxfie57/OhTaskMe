from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.utils import timezone
from users.models import User
from tasks.models import Task
from events.models import Event
from datetime import datetime, timedelta, date
import pytz
import json
import calendar

def home(request):
    """
    Landing page for non-authenticated users.
    Redirects to dashboard if user is authenticated.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'base/home.html')

@login_required
def dashboard(request):
    """
    Dashboard view showing task and event statistics and upcoming items.
    """
    user = request.user
    now = datetime.now(pytz.timezone(user.timezone))
    
    # Get task statistics
    all_tasks = Task.objects.filter(owner=user)
    completed_tasks = all_tasks.filter(completed=True)
    pending_tasks = all_tasks.filter(completed=False)
    
    task_count = all_tasks.count()
    completed_task_count = completed_tasks.count()
    pending_task_count = pending_tasks.count()
    
    completion_percentage = 0
    if task_count > 0:
        completion_percentage = int((completed_task_count / task_count) * 100)
    
    # Get upcoming tasks
    upcoming_tasks = pending_tasks.filter(scheduled_time__gte=now).order_by('scheduled_time')[:5]
    
    # Get event statistics
    all_events = Event.objects.filter(owner=user)
    upcoming_events = all_events.filter(start_time__gte=now)
    
    event_count = all_events.count()
    upcoming_event_count = upcoming_events.count()
    
    # Get upcoming events
    upcoming_events = upcoming_events.order_by('start_time')[:5]
    
    # Weekly task completion data
    one_week_ago = now - timedelta(days=7)
    tasks_completed_by_day = {}
    tasks_completed_this_week = 0
    
    for i in range(7):
        day = one_week_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = completed_tasks.filter(
            scheduled_time__gte=day_start,
            scheduled_time__lte=day_end
        ).count()
        
        tasks_completed_by_day[day.strftime('%a')] = count
        tasks_completed_this_week += count
    
    weekly_labels = json.dumps(list(tasks_completed_by_day.keys()))
    weekly_data = json.dumps(list(tasks_completed_by_day.values()))
    
    context = {
        'task_count': task_count,
        'completed_task_count': completed_task_count,
        'pending_task_count': pending_task_count,
        'completion_percentage': completion_percentage,
        'upcoming_tasks': upcoming_tasks,
        'event_count': event_count,
        'upcoming_event_count': upcoming_event_count,
        'upcoming_events': upcoming_events,
        'tasks_completed_this_week': tasks_completed_this_week,
        'weekly_labels': weekly_labels,
        'weekly_data': weekly_data,
        'now': now,
    }
    
    return render(request, 'base/dashboard.html', context)

def login_view(request):
    """
    Login view for user authentication.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to the next page if provided, otherwise to dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')

def logout_view(request):
    """
    Logout view to end user session.
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

def register(request):
    """
    User registration view.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    timezones = pytz.common_timezones
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        timezone = request.POST.get('timezone', 'UTC')
        
        # Basic validation
        if not username or not email or not password1:
            messages.error(request, 'Please fill in all required fields.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use.')
        else:
            # Create the user
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    timezone=timezone
                )
                login(request, user)
                messages.success(request, f'Account created successfully! Welcome, {username}!')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'users/register.html', {'timezones': timezones})

@login_required
def profile(request):
    """
    User profile view and update.
    """
    user = request.user
    timezones = pytz.common_timezones
    
    if request.method == 'POST':
        # Update user profile
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.timezone = request.POST.get('timezone', user.timezone)
        
        try:
            user.save()
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return render(request, 'users/profile.html', {'timezones': timezones})

@login_required
def password_change(request):
    """
    Change password view.
    """
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Basic validation
        if not old_password or not new_password1 or not new_password2:
            messages.error(request, 'Please fill in all fields.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        elif not request.user.check_password(old_password):
            messages.error(request, 'Incorrect current password.')
        else:
            # Change password
            request.user.set_password(new_password1)
            request.user.save()
            login(request, request.user)  # Re-login user with new password
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    
    return render(request, 'users/password_change.html')

def password_reset_request(request):
    """
    Password reset request view.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Please enter your email address.')
        else:
            users = User.objects.filter(email=email)
            
            if users.exists():
                # In a real app, send password reset email here
                messages.success(request, 'Password reset link has been sent to your email.')
            else:
                # Don't reveal that an email doesn't exist for security
                messages.success(request, 'Password reset link has been sent to your email.')
    
    return render(request, 'users/password_reset.html')

def password_reset_confirm(request, uidb64, token):
    """
    Password reset confirmation view.
    """
    # In a real app, validate the token and user here
    
    if request.method == 'POST':
        password1 = request.POST.get('new_password1')
        password2 = request.POST.get('new_password2')
        
        if not password1 or not password2:
            messages.error(request, 'Please fill in all fields.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        else:
            # In a real app, reset the password here
            messages.success(request, 'Password has been reset successfully!')
            return redirect('login')
    
    return render(request, 'users/password_reset_confirm.html')

def about(request):
    """
    About page view.
    """
    return render(request, 'base/about.html')

def privacy(request):
    """
    Privacy policy view.
    """
    return render(request, 'base/privacy.html')

def terms(request):
    """
    Terms of service view.
    """
    return render(request, 'base/terms.html')


# ===== TASK VIEWS =====

# Date format constant
DATETIME_FORMAT = '%Y-%m-%dT%H:%M'

@login_required
def task_list(request):
    """
    Display list of tasks with filtering and sorting options.
    """
    user = request.user
    tasks = Task.objects.filter(owner=user)
    
    # Handle filtering
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', '')
    event_filter = request.GET.get('event', '')
    search_query = request.GET.get('search', '')
    
    if status_filter == 'completed':
        tasks = tasks.filter(completed=True)
    elif status_filter == 'pending':
        tasks = tasks.filter(completed=False)
    elif status_filter == 'overdue':
        now = datetime.now(pytz.timezone(user.timezone))
        tasks = tasks.filter(completed=False, scheduled_time__lt=now)
    
    if date_filter:
        try:
            filter_date = parse_date(date_filter)
            if filter_date:
                tasks = tasks.filter(scheduled_time__date=filter_date)
        except ValueError:
            pass
    
    if event_filter:
        try:
            event_id = int(event_filter)
            tasks = tasks.filter(event=event_id)
        except (ValueError, TypeError):
            pass
    
    if search_query:
        tasks = tasks.filter(Q(description__icontains=search_query))
    
    # Handle sorting
    sort_by = request.GET.get('sort', 'scheduled_time')
    if sort_by in ['description', 'scheduled_time', 'created_at', '-description', '-scheduled_time', '-created_at']:
        tasks = tasks.order_by(sort_by)
    else:
        tasks = tasks.order_by('scheduled_time')
    
    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get events for filter dropdown
    events = Event.objects.filter(owner=user).order_by('description')
    
    context = {
        'page_obj': page_obj,
        'tasks': page_obj,
        'events': events,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'event_filter': event_filter,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'tasks/task_list.html', context)

@login_required
def task_detail(request, task_id):
    """
    Display detailed view of a specific task.
    """
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    
    context = {
        'task': task,
    }
    
    return render(request, 'tasks/task_detail.html', context)

@login_required
def task_create(request):
    """
    Create a new task.
    """
    if request.method == 'POST':
        description = request.POST.get('description')
        scheduled_time = request.POST.get('scheduled_time')
        event_id = request.POST.get('event')
        
        # Validation
        if not description:
            messages.error(request, 'Task description is required.')
        elif not scheduled_time:
            messages.error(request, 'Scheduled time is required.')
        else:
            try:
                # Parse the datetime - try multiple formats
                scheduled_dt = None
                
                # Try different datetime formats
                formats_to_try = [
                    DATETIME_FORMAT,  # '%Y-%m-%dT%H:%M'
                    '%B %d, %Y at %I:%M %p',  # 'August 18, 2025 at 3:00 PM'
                    '%Y-%m-%d %H:%M',  # '2025-08-18 15:00'
                    '%m/%d/%Y %I:%M %p',  # '08/18/2025 3:00 PM'
                    '%d/%m/%Y %H:%M',  # '18/08/2025 15:00'
                ]
                
                for fmt in formats_to_try:
                    try:
                        scheduled_dt = datetime.strptime(scheduled_time, fmt)
                        break
                    except ValueError:
                        continue
                
                if scheduled_dt is None:
                    raise ValueError("Could not parse datetime format")
                
                user_tz = pytz.timezone(request.user.timezone)
                scheduled_dt = user_tz.localize(scheduled_dt)
                
                # Create the task
                task_data = {
                    'description': description,
                    'scheduled_time': scheduled_dt,
                    'owner': request.user,
                }
                
                # Handle event assignment
                if event_id:
                    try:
                        event = Event.objects.get(id=event_id, owner=request.user)
                        task_data['event'] = event
                    except Event.DoesNotExist:
                        pass  # Leave event as None
                
                task = Task.objects.create(**task_data)
                
                messages.success(request, f'Task "{task.description}" created successfully!')
                return redirect('task_detail', task_id=task.pk)
                
            except ValueError as e:
                messages.error(request, 'Invalid date/time format.')
            except Exception as e:
                messages.error(request, f'Error creating task: {str(e)}')
    
    # Get events for the form
    events = Event.objects.filter(owner=request.user).order_by('description')
    
    context = {
        'events': events,
    }
    
    return render(request, 'tasks/task_create.html', context)

@login_required
def task_edit(request, task_id):
    """
    Edit an existing task.
    """
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    
    if request.method == 'POST':
        description = request.POST.get('description')
        scheduled_time = request.POST.get('scheduled_time')
        event_id = request.POST.get('event')
        completed = request.POST.get('completed') == 'on'
        
        # Validation
        if not description:
            messages.error(request, 'Task description is required.')
        elif not scheduled_time:
            messages.error(request, 'Scheduled time is required.')
        else:
            try:
                # Parse the datetime - try multiple formats
                scheduled_dt = None
                
                # Try different datetime formats
                formats_to_try = [
                    DATETIME_FORMAT,  # '%Y-%m-%dT%H:%M'
                    '%B %d, %Y at %I:%M %p',  # 'August 18, 2025 at 3:00 PM'
                    '%Y-%m-%d %H:%M',  # '2025-08-18 15:00'
                    '%m/%d/%Y %I:%M %p',  # '08/18/2025 3:00 PM'
                    '%d/%m/%Y %H:%M',  # '18/08/2025 15:00'
                ]
                
                for fmt in formats_to_try:
                    try:
                        scheduled_dt = datetime.strptime(scheduled_time, fmt)
                        break
                    except ValueError:
                        continue
                
                if scheduled_dt is None:
                    raise ValueError("Could not parse datetime format")
                
                user_tz = pytz.timezone(request.user.timezone)
                scheduled_dt = user_tz.localize(scheduled_dt)
                
                # Update the task
                update_data = {
                    'description': description,
                    'scheduled_time': scheduled_dt,
                    'completed': completed,
                }
                
                # Handle event assignment
                if event_id:
                    try:
                        event = Event.objects.get(id=event_id, owner=request.user)
                        update_data['event'] = event
                    except Event.DoesNotExist:
                        update_data['event'] = None
                else:
                    update_data['event'] = None
                
                # Update fields
                for field, value in update_data.items():
                    setattr(task, field, value)
                task.save()
                
                messages.success(request, f'Task "{task.description}" updated successfully!')
                return redirect('task_detail', task_id=task.pk)
                
            except ValueError:
                messages.error(request, 'Invalid date/time format.')
            except Exception as e:
                messages.error(request, f'Error updating task: {str(e)}')
    
    # Get events for the form
    events = Event.objects.filter(owner=request.user).order_by('description')
    
    # Format the scheduled time for the form
    user_tz = pytz.timezone(request.user.timezone)
    scheduled_time_local = task.scheduled_time.astimezone(user_tz)
    
    context = {
        'task': task,
        'events': events,
        'scheduled_time_formatted': scheduled_time_local.strftime(DATETIME_FORMAT),
    }
    
    return render(request, 'tasks/task_edit.html', context)

@login_required
def task_delete(request, task_id):
    """
    Delete a task.
    """
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    
    if request.method == 'POST':
        task_description = task.description
        task.delete()
        messages.success(request, f'Task "{task_description}" deleted successfully!')
        return redirect('task_list')
    
    context = {
        'task': task,
    }
    
    return render(request, 'tasks/task_delete.html', context)

@login_required
def task_toggle(request, task_id):
    """
    Toggle task completion status.
    """
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    task.completed = not task.completed
    task.save()
    
    status = "completed" if task.completed else "pending"
    messages.success(request, f'Task "{task.description}" marked as {status}!')
    
    return redirect('task_list')

@login_required
@require_POST
def ajax_task_toggle(request):
    """
    AJAX endpoint to toggle task completion status.
    """
    try:
        task_id = request.POST.get('task_id')
        task = get_object_or_404(Task, id=task_id, owner=request.user)
        task.completed = not task.completed
        task.save()
        
        return JsonResponse({
            'success': True,
            'completed': task.completed,
            'message': f'Task marked as {"completed" if task.completed else "pending"}'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def task_calendar(request):
    """
    Display tasks in a calendar view.
    """
    user = request.user
    user_tz = pytz.timezone(user.timezone)
    
    # Get current month and year from URL parameters
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    
    # Create calendar
    cal = calendar.Calendar(firstweekday=6)  # Start with Sunday
    month_days = cal.monthdayscalendar(year, month)
    
    # Get tasks for this month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    tasks = Task.objects.filter(
        owner=user,
        scheduled_time__date__gte=start_date,
        scheduled_time__date__lt=end_date
    ).order_by('scheduled_time')
    
    # Group tasks by day
    tasks_by_day = {}
    for task in tasks:
        task_date = task.scheduled_time.astimezone(user_tz).date()
        day = task_date.day
        if day not in tasks_by_day:
            tasks_by_day[day] = []
        tasks_by_day[day].append(task)
    
    # Calculate previous and next month
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'month_days': month_days,
        'tasks_by_day': tasks_by_day,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'weekday_names': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    }
    
    return render(request, 'tasks/task_calendar.html', context)


# ===========================
# EVENT VIEWS
# ===========================

@login_required
def event_list(request):
    """
    Display a list of events with filtering and sorting options.
    """
    user = request.user
    events = Event.objects.filter(owner=user)
    
    # Apply filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('search')
    
    if date_from:
        try:
            date_from_parsed = parse_date(date_from)
            if date_from_parsed:
                events = events.filter(start_time__date__gte=date_from_parsed)
        except (ValueError, TypeError):
            pass
    
    if date_to:
        try:
            date_to_parsed = parse_date(date_to)
            if date_to_parsed:
                events = events.filter(start_time__date__lte=date_to_parsed)
        except (ValueError, TypeError):
            pass
    
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'start_time')
    if sort_by in ['start_time', '-start_time', 'title', '-title', 'created_at', '-created_at']:
        events = events.order_by(sort_by)
    else:
        events = events.order_by('start_time')
    
    # Pagination
    paginator = Paginator(events, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'events': page_obj,
    }
    
    return render(request, 'events/event_list.html', context)


@login_required
def event_detail(request, event_id):
    """
    Display detailed information about a specific event.
    """
    event = get_object_or_404(Event, id=event_id, owner=request.user)
    
    # Get associated tasks
    associated_tasks = event.get_tasks().order_by('scheduled_time')
    
    # Check if we should auto-open AI suggestions
    show_ai_suggestions = request.session.pop('show_ai_suggestions', False)
    
    context = {
        'event': event,
        'associated_tasks': associated_tasks,
        'show_ai_suggestions': show_ai_suggestions,
    }
    
    return render(request, 'events/event_detail.html', context)


@login_required
def event_create(request):
    """
    Create a new event.
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        location = request.POST.get('location', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        task_generation_type = request.POST.get('task_generation_type', 'none')
        
        # Validate required fields
        if not all([title, start_time, end_time]):
            messages.error(request, 'Title, start time, and end time are required.')
            return render(request, 'events/event_create.html')
        
        try:
            # Parse datetime strings
            start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Validate end time is after start time
            if end_datetime <= start_datetime:
                messages.error(request, 'End time must be after start time.')
                return render(request, 'events/event_create.html')
            
            # Create event
            event = Event.objects.create(
                title=title,
                description=description,
                location=location,
                start_time=start_datetime,
                end_time=end_datetime,
                owner=request.user
            )
            
            # Handle task generation based on user choice
            if task_generation_type == 'standard':
                # Generate standard preparation tasks
                tasks = event.generate_preparation_tasks()
                messages.success(
                    request, 
                    f'Event "{event.title}" created successfully with {len(tasks)} preparation tasks!'
                )
                return redirect('event_detail', event_id=event.id)
                
            elif task_generation_type == 'ai':
                # Redirect to event detail with AI suggestion modal
                messages.success(request, f'Event "{event.title}" created successfully! AI task suggestions are being generated...')
                # Store a session flag to auto-open AI suggestions
                request.session['show_ai_suggestions'] = True
                return redirect('event_detail', event_id=event.id)
                
            else:
                # No tasks generated
                messages.success(request, f'Event "{event.title}" created successfully!')
                return redirect('event_detail', event_id=event.id)
            
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid date/time format: {str(e)}')
            return render(request, 'events/event_create.html')
    
    return render(request, 'events/event_create.html')


@login_required
def event_edit(request, event_id):
    """
    Edit an existing event.
    """
    event = get_object_or_404(Event, id=event_id, owner=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        location = request.POST.get('location', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        # Validate required fields
        if not all([title, start_time, end_time]):
            messages.error(request, 'Title, start time, and end time are required.')
            return render(request, 'events/event_edit.html', {'event': event})
        
        try:
            # Parse datetime strings
            start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Validate end time is after start time
            if end_datetime <= start_datetime:
                messages.error(request, 'End time must be after start time.')
                return render(request, 'events/event_edit.html', {'event': event})
            
            # Update event
            event.title = title
            event.description = description
            event.location = location
            event.start_time = start_datetime
            event.end_time = end_datetime
            event.save()
            
            messages.success(request, f'Event "{event.title}" updated successfully!')
            return redirect('event_detail', event_id=event.id)
            
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid date/time format: {str(e)}')
            return render(request, 'events/event_edit.html', {'event': event})
    
    context = {
        'event': event,
    }
    
    return render(request, 'events/event_edit.html', context)


@login_required
def event_delete(request, event_id):
    """
    Delete an event.
    """
    event = get_object_or_404(Event, id=event_id, owner=request.user)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" has been deleted.')
        return redirect('event_list')
    
    context = {
        'event': event,
    }
    
    return render(request, 'events/event_delete.html', context)


@login_required
def event_calendar(request):
    """
    Display events in a calendar format.
    """
    user = request.user
    
    # Get year and month from query parameters or use current
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    
    # Get events for the month
    month_start = datetime(year, month, 1, tzinfo=pytz.timezone(user.timezone))
    if month == 12:
        month_end = datetime(year + 1, 1, 1, tzinfo=pytz.timezone(user.timezone)) - timedelta(seconds=1)
    else:
        month_end = datetime(year, month + 1, 1, tzinfo=pytz.timezone(user.timezone)) - timedelta(seconds=1)
    
    events = Event.objects.filter(
        owner=user,
        start_time__range=(month_start, month_end)
    ).order_by('start_time')
    
    # Group events by day
    events_by_day = {}
    for event in events:
        day = event.start_time.day
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)
    
    # Generate calendar structure
    cal = calendar.Calendar(firstweekday=6)  # Start week on Sunday
    month_days = list(cal.itermonthdays(year, month))
    
    # Calculate previous and next month
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'month_days': month_days,
        'events_by_day': events_by_day,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'weekday_names': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    }
    
    return render(request, 'events/event_calendar.html', context)


@login_required
def integrated_calendar(request):
    """
    Display both tasks and events in a unified calendar view.
    Supports monthly, weekly, and daily views with filtering options.
    """
    # Get view type (month, week, day)
    view_type = request.GET.get('view', 'month')
    
    # Get current date parameters
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    day = int(request.GET.get('day', today.day))
    
    # Get filter parameters
    show_tasks = request.GET.get('show_tasks', 'true').lower() == 'true'
    show_events = request.GET.get('show_events', 'true').lower() == 'true'
    show_completed = request.GET.get('show_completed', 'false').lower() == 'true'
    
    current_date = date(year, month, day)
    
    if view_type == 'month':
        # Month view
        cal = calendar.Calendar(firstweekday=6)  # Start with Sunday
        month_days = cal.monthdayscalendar(year, month)
        
        # Get start and end dates for the month view
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timezone.timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timezone.timedelta(days=1)
            
    elif view_type == 'week':
        # Week view - get the week containing the current day
        start_date = current_date - timezone.timedelta(days=current_date.weekday() + 1)  # Start on Sunday
        end_date = start_date + timezone.timedelta(days=6)
        
        # Generate week days
        week_days = []
        for i in range(7):
            week_days.append(start_date + timezone.timedelta(days=i))
            
    else:  # day view
        start_date = current_date
        end_date = current_date
    
    # Fetch tasks and events based on filters
    calendar_items = []
    
    if show_tasks:
        tasks_query = Task.objects.filter(
            owner=request.user,
            scheduled_time__date__gte=start_date,
            scheduled_time__date__lte=end_date
        )
        
        if not show_completed:
            tasks_query = tasks_query.filter(completed=False)
            
        tasks = tasks_query.order_by('scheduled_time')
        
        for task in tasks:
            calendar_items.append({
                'type': 'task',
                'id': task.id,
                'title': task.description,  # Task uses 'description' field
                'description': task.description,
                'date': task.scheduled_time.date(),
                'time': task.scheduled_time.time(),
                'datetime': task.scheduled_time,
                'completed': task.completed,
                'event_id': task.event.id if task.event else None,
                'event_title': task.event.title if task.event else None,
                'css_class': 'calendar-task-completed' if task.completed else 'calendar-task',
                'color': 'success' if task.completed else 'primary'
            })
    
    if show_events:
        events = Event.objects.filter(
            owner=request.user,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date  # Changed from end_time to start_time for proper filtering
        ).order_by('start_time')
        
        for event in events:
            calendar_items.append({
                'type': 'event',
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'date': event.start_time.date(),
                'time': event.start_time.time(),
                'datetime': event.start_time,
                'end_time': event.end_time,
                'location': event.location,
                'is_active': False,  # Default to False since is_active field doesn't exist yet
                'css_class': 'calendar-event',  # Use standard event styling for now
                'color': 'info'  # Use info color for all events for now
            })
    
    # Sort all items by datetime
    calendar_items.sort(key=lambda x: x['datetime'])
    
    # Group items by date for easy template rendering
    items_by_date = {}
    for item in calendar_items:
        item_date = item['date']
        if item_date not in items_by_date:
            items_by_date[item_date] = []
        items_by_date[item_date].append(item)
    
    # Calculate navigation dates
    if view_type == 'month':
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        nav_prev = {'year': prev_year, 'month': prev_month, 'day': day}
        nav_next = {'year': next_year, 'month': next_month, 'day': day}
        
    elif view_type == 'week':
        prev_date = start_date - timezone.timedelta(days=7)
        next_date = start_date + timezone.timedelta(days=7)
        
        nav_prev = {'year': prev_date.year, 'month': prev_date.month, 'day': prev_date.day}
        nav_next = {'year': next_date.year, 'month': next_date.month, 'day': next_date.day}
        
    else:  # day view
        prev_date = current_date - timezone.timedelta(days=1)
        next_date = current_date + timezone.timedelta(days=1)
        
        nav_prev = {'year': prev_date.year, 'month': prev_date.month, 'day': prev_date.day}
        nav_next = {'year': next_date.year, 'month': next_date.month, 'day': next_date.day}
    
    # Get user preferences (for future use)
    calendar_preferences = getattr(request.user, 'calendar_preferences', {})
    
    context = {
        'view_type': view_type,
        'current_date': current_date,
        'today': today,
        'year': year,
        'month': month,
        'day': day,
        'month_name': calendar.month_name[month],
        'start_date': start_date,
        'end_date': end_date,
        'calendar_items': calendar_items,
        'items_by_date': items_by_date,
        'show_tasks': show_tasks,
        'show_events': show_events,
        'show_completed': show_completed,
        'nav_prev': nav_prev,
        'nav_next': nav_next,
        'calendar_preferences': calendar_preferences,
    }
    
    # Add view-specific context
    if view_type == 'month':
        context.update({
            'month_days': month_days,
            'weekday_names': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        })
    elif view_type == 'week':
        context.update({
            'week_days': week_days,
            'weekday_names': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        })
    
    return render(request, 'calendar/integrated_calendar.html', context)


@login_required
@require_POST
def generate_event_tasks(request, event_id):
    """
    Generate preparation tasks for an event via AJAX.
    """
    event = get_object_or_404(Event, id=event_id, owner=request.user)
    
    try:
        tasks = event.generate_preparation_tasks()
        return JsonResponse({
            'success': True,
            'message': f'Generated {len(tasks)} preparation tasks for "{event.title}"',
            'task_count': len(tasks)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error generating tasks: {str(e)}'
        })


@login_required
@require_POST
def suggest_event_tasks(request, event_id):
    """
    Generate AI-based task suggestions for an event via AJAX.
    
    TODO: Integrate with user profile for personalized suggestions
    TODO: Add machine learning model for better task prediction
    TODO: Implement user behavior tracking for adaptive learning
    TODO: Add schedule analysis to avoid conflicts and optimize timing
    """
    event = get_object_or_404(Event, id=event_id, owner=request.user)
    
    try:
        suggestions = event.suggest_tasks()
        
        # Format suggestions for JSON response
        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestions.append({
                'description': suggestion['description'],
                'scheduled_time': suggestion['scheduled_time'].strftime('%Y-%m-%d %H:%M'),
                'confidence': round(suggestion['confidence'], 1),  # Already in percentage format
                'relation': suggestion['relation']
            })
        
        return JsonResponse({
            'success': True,
            'suggestions': formatted_suggestions,
            'message': f'Generated {len(suggestions)} AI task suggestions for "{event.title}"'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error generating AI suggestions: {str(e)}',
            'suggestions': []
        })


@login_required
@require_POST
def create_suggested_tasks(request, event_id):
    """
    Create tasks from AI suggestions via AJAX.
    """
    event = get_object_or_404(Event, id=event_id, owner=request.user)
    
    try:
        # Get selected task indices from POST data
        selected_indices = request.POST.getlist('selected_tasks[]')
        suggestions = event.suggest_tasks()
        
        created_tasks = []
        for index_str in selected_indices:
            try:
                index = int(index_str)
                if 0 <= index < len(suggestions):
                    suggestion = suggestions[index]
                    
                    # Create the task
                    task = Task.objects.create(
                        description=suggestion['description'],
                        scheduled_time=suggestion['scheduled_time'],
                        owner=request.user,
                        event=event
                    )
                    created_tasks.append(task)
                    
            except (ValueError, IndexError):
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Created {len(created_tasks)} tasks from AI suggestions',
            'task_count': len(created_tasks)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating tasks: {str(e)}'
        })
