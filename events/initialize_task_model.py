"""
Script to initialize the task suggestion model with sample data.

This should be run once when setting up the application for the first time.
"""
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ohtaskme.settings')
django.setup()

from events.initial_training_data import save_initial_training_data, INITIAL_TRAINING_DATA
from events.training_pipeline import train_model

def initialize_model():
    """
    Initialize the task suggestion model with sample data.
    """
    print("Initializing task suggestion model...")
    
    # Save initial training data
    data_path = save_initial_training_data()
    print(f"Initial training data saved to {data_path}")
    
    # Train the model
    model_path = train_model()
    print(f"Initial model trained and saved to {model_path}")
    
    print(f"Model initialization complete! {len(INITIAL_TRAINING_DATA)} event types and sample tasks processed.")

if __name__ == '__main__':
    initialize_model()
