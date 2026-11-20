"""Admin configuration for managing users, publishers, and content.

Registers the CustomUser, Publisher, Article, and Newsletter models
with the Django admin site and customizes their list displays,
filters, search fields, fieldsets, and horizontal relation widgets.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Publisher, Article, Newsletter


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser roles and subscriptions."""

    fieldsets = UserAdmin.fieldsets + (
        (
            "Role & Subscriptions",
            {
                "fields": (
                    "role",
                    "subscribed_publishers",
                    "subscribed_journalists",
                ),
            },
        ),
    )
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    # Adds the dual-column chooser
    filter_horizontal = ("subscribed_publishers", "subscribed_journalists")


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin configuration for Publisher editors and journalists."""

    list_display = ("name", "created_at")
    filter_horizontal = ("editors", "journalists")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin configuration for Article filtering and search."""

    list_display = ("title", "author", "publisher", "approved", "created_at")
    list_filter = ("approved", "publisher", "created_at")
    search_fields = ("title", "content")


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin configuration for Newsletter records and articles."""

    list_display = ("title", "author", "created_at")
    filter_horizontal = ("articles",)
