"""Application configuration for the news Django app.

Defines the NewsConfig class to configure app metadata and connect
signal handlers on startup.
"""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Configuration class for the news application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "news"

    def ready(self):
        """Import signal handlers when the application is ready."""
        import news.signals  # noqa
