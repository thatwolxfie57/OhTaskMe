"""
Management command to train the task suggestion model.
"""
from django.core.management.base import BaseCommand
from events.training_pipeline import train_model

class Command(BaseCommand):
    help = 'Train the task suggestion model based on historical data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting model training...'))
        
        try:
            model_path = train_model()
            self.stdout.write(self.style.SUCCESS(f'Model training completed! Model saved to {model_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during model training: {str(e)}'))
