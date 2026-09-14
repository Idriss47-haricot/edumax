from django.apps import AppConfig


from django.apps import AppConfig

class WebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'website'
    
    def ready(self):
        # Ceci active les signaux au démarrage de Django
        import website.signals
