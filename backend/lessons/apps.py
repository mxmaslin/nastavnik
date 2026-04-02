from django.apps import AppConfig


class LessonsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lessons'
    verbose_name = 'Lessons'

    def ready(self):
        from lessons import timeout_handler
        timeout_handler.timeout_handler.start()
