from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "content"

    def ready(self):
        from .roles import ensure_content_staff_group

        post_migrate.connect(ensure_content_staff_group, dispatch_uid="content.ensure_content_staff_group")
