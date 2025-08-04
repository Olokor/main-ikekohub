from django.apps import AppConfig


class StudentAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'student_app'

    def ready(self):
        import admin_app.signals