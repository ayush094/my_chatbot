from django.apps import AppConfig
from django.db import connection


class ChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chat"

    def ready(self):
        # We don't perform DB operations here as it blocks migrations and command startup
        pass
