from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from news.models import Article, Newsletter, Publisher


class Command(BaseCommand):
    help = (
        "Sets up default user groups and model permissions for "
        "Reader, Editor, and Journalist roles."
    )

    def handle(self, *args, **options):
        # 1. Fetch content types for our models
        article_ct = ContentType.objects.get_for_model(Article)
        newsletter_ct = ContentType.objects.get_for_model(Newsletter)
        publisher_ct = ContentType.objects.get_for_model(Publisher)

        # 2. Define permission sets per role
        # Reader: View only
        reader_group, _ = Group.objects.get_or_create(name="Reader")
        reader_perms = Permission.objects.filter(
            content_type__in=[article_ct, newsletter_ct, publisher_ct],
            codename__startswith="view_",
        )
        reader_group.permissions.set(reader_perms)

        # Journalist: Add, View, Change, Delete
        journalist_group, _ = Group.objects.get_or_create(name="Journalist")
        journalist_perms = Permission.objects.filter(
            content_type__in=[article_ct, newsletter_ct],
            codename__in=[
                "add_article",
                "view_article",
                "change_article",
                "delete_article",
                "add_newsletter",
                "view_newsletter",
                "change_newsletter",
                "delete_newsletter",
            ],
        )
        journalist_group.permissions.set(journalist_perms)

        # Editor: View, Change, Delete
        editor_group, _ = Group.objects.get_or_create(name="Editor")
        editor_perms = Permission.objects.filter(
            content_type__in=[article_ct, newsletter_ct, publisher_ct],
            codename__in=[
                "view_article",
                "change_article",
                "delete_article",
                "view_newsletter",
                "change_newsletter",
                "delete_newsletter",
                "view_publisher",
                "change_publisher",
            ],
        )
        editor_group.permissions.set(editor_perms)

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully configured groups and permissions."
            )
        )
