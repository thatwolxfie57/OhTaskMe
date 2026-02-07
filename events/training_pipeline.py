"""
Training pipeline for the task suggestion model.

This module handles the collection of historical task data and
training of models to improve task suggestions over time.
"""
import os
import pickle
import json
import datetime
from django.utils import timezone
from django.db.models import Count, Q
from django.conf import settings

from events.models import Event
from tasks.models import Task

# Create a directory for ML models if it doesn't exist
MODEL_DIR = os.path.join(settings.BASE_DIR, 'ml_models')
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

def collect_training_data():
    """
    Collect historical event and task data for training.
    
    Returns:
        Dictionary containing training data
    """
    # Get events with associated tasks
    events_with_tasks = Event.objects.annotate(
        task_count=Count('tasks')
    ).filter(task_count__gt=0)
    
    training_data = []
    
    for event in events_with_tasks:
        # Get tasks associated with this event
        tasks = Task.objects.filter(event=event)
        
        # Extract features from event
        event_data = {
            'title': event.title,
            'description': event.description,
            'start_time': event.start_time.isoformat(),
            'end_time': event.end_time.isoformat(),
            'tasks': []
        }
        
        # Extract task information
        for task in tasks:
            task_data = {
                'description': task.description,
                'scheduled_time': task.scheduled_time.isoformat(),
                'completed': task.completed,
                'relation': 'before' if task.scheduled_time < event.start_time else 'after'
            }
            event_data['tasks'].append(task_data)
        
        training_data.append(event_data)
    
    return training_data

def save_training_data(training_data):
    """
    Save the collected training data to a file.
    
    Args:
        training_data: Dictionary containing the training data
    """
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(MODEL_DIR, f'training_data_{timestamp}.json')
    
    with open(filepath, 'w') as f:
        json.dump(training_data, f, indent=2)
    
    return filepath

def extract_pattern_frequencies(training_data):
    """
    Extract frequencies of task patterns from training data.
    
    Args:
        training_data: Dictionary containing the training data
        
    Returns:
        Dictionary with pattern frequencies
    """
    pattern_frequencies = {}
    
    for event_data in training_data:
        # Extract words from event title and description
        event_text = f"{event_data['title']} {event_data['description']}".lower()
        
        # Check which patterns match this event
        from events.task_suggestions import EVENT_PATTERNS
        matching_patterns = []
        
        for pattern in EVENT_PATTERNS.keys():
            import re
            if re.search(pattern, event_text):
                matching_patterns.append(pattern)
        
        # If no patterns match, use the default pattern
        if not matching_patterns:
            matching_patterns = [r".*"]
        
        # Count task frequencies for each pattern
        for pattern in matching_patterns:
            if pattern not in pattern_frequencies:
                pattern_frequencies[pattern] = {
                    'count': 0,
                    'tasks': {}
                }
            
            pattern_frequencies[pattern]['count'] += 1
            
            # Count task frequencies
            for task in event_data['tasks']:
                task_desc = task['description']
                if task_desc in pattern_frequencies[pattern]['tasks']:
                    pattern_frequencies[pattern]['tasks'][task_desc] += 1
                else:
                    pattern_frequencies[pattern]['tasks'][task_desc] = 1
    
    return pattern_frequencies

def train_model():
    """
    Train a model for task suggestions based on historical data.
    
    Returns:
        Path to the saved model file
    """
    # Collect training data
    training_data = collect_training_data()
    
    # Save the training data
    data_filepath = save_training_data(training_data)
    
    # Extract pattern frequencies
    pattern_frequencies = extract_pattern_frequencies(training_data)
    
    # Save the trained model (pattern frequencies)
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    model_filepath = os.path.join(MODEL_DIR, f'task_suggestion_model_{timestamp}.pkl')
    
    with open(model_filepath, 'wb') as f:
        pickle.dump(pattern_frequencies, f)
    
    return model_filepath

def load_latest_model():
    """
    Load the latest trained model.
    
    Returns:
        Loaded model or None if no model exists
    """
    model_files = [f for f in os.listdir(MODEL_DIR) if f.startswith('task_suggestion_model_')]
    
    if not model_files:
        return None
    
    # Get the most recent model file
    latest_model = sorted(model_files)[-1]
    model_path = os.path.join(MODEL_DIR, latest_model)
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return model

def update_model_with_feedback(accepted_tasks, rejected_tasks, event):
    """
    Update the model based on user feedback.
    
    Args:
        accepted_tasks: List of accepted task suggestions
        rejected_tasks: List of rejected task suggestions
        event: The Event object
        
    Returns:
        Path to the updated model file
    """
    # Load the latest model
    model = load_latest_model()
    
    if not model:
        # If no model exists, create a new one
        return train_model()
    
    # Extract event text
    event_text = f"{event.title} {event.description}".lower()
    
    # Find matching patterns
    from events.task_suggestions import EVENT_PATTERNS
    matching_patterns = []
    
    for pattern in EVENT_PATTERNS.keys():
        import re
        if re.search(pattern, event_text):
            matching_patterns.append(pattern)
    
    # If no patterns match, use the default pattern
    if not matching_patterns:
        matching_patterns = [r".*"]
    
    # Update model with feedback
    for pattern in matching_patterns:
        if pattern not in model:
            model[pattern] = {
                'count': 0,
                'tasks': {}
            }
        
        model[pattern]['count'] += 1
        
        # Increase count for accepted tasks
        for task in accepted_tasks:
            task_desc = task['description']
            if task_desc in model[pattern]['tasks']:
                model[pattern]['tasks'][task_desc] += 1
            else:
                model[pattern]['tasks'][task_desc] = 1
    
    # Save the updated model
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    model_filepath = os.path.join(MODEL_DIR, f'task_suggestion_model_{timestamp}.pkl')
    
    with open(model_filepath, 'wb') as f:
        pickle.dump(model, f)
    
    return model_filepath
