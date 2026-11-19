from django.apps import AppConfig


class FormacionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "formacion"
    verbose_name = "Formación"

    def ready(self):
        from . import signals  # noqa: F401
