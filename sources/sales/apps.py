from django.apps import AppConfig


class SalesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales'

    def ready(self):
        # Cette méthode est appelée quand Django démarre
        import sales.signals  # On importe les signaux ici