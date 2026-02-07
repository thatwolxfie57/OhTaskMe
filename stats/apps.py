from django.apps import AppConfig


class StatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stats'
    
    def ready(self):
        """Import signals when the app is ready."""
        import stats.signals
