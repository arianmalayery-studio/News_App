from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class Publisher(models.Model):
    """Publishers curate articles and have affiliated editors and
    journalists[cite: 4]."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # A publisher can have multiple editors and journalists[cite: 4]
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="publisher_editors",
        blank=True,
        limit_choices_to={"role": "EDITOR"},
    )
    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="publisher_journalists",
        blank=True,
        limit_choices_to={"role": "JOURNALIST"},
    )

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """Custom user model supporting Reader, Editor, and Journalist roles[cite:
    4, 5]."""

    class Role(models.TextChoices):
        READER = "READER", "Reader"
        EDITOR = "EDITOR", "Editor"
        JOURNALIST = "JOURNALIST", "Journalist"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.READER
    )

    # Reader-specific subscription fields[cite: 6]
    subscribed_publishers = models.ManyToManyField(
        Publisher, related_name="reader_subscribers", blank=True
    )
    subscribed_journalists = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="reader_subscribers",
        blank=True,
        limit_choices_to={"role": "JOURNALIST"},
    )

    def clean(self):
        super().clean()
        # Enforce requirement: non-reader roles should have subscription fields
        # cleared[cite: 6]
        if self.role != self.Role.READER and self.pk:
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Clear subscription relationships if role is not Reader[cite: 6]
        if not is_new and self.role != self.Role.READER:
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

        # Automatically synchronize the user with their matching Django Auth
        # Group[cite: 4, 5]
        role_group_map = {
            self.Role.READER: "Reader",
            self.Role.EDITOR: "Editor",
            self.Role.JOURNALIST: "Journalist",
        }
        target_group_name = role_group_map.get(self.role)
        if target_group_name:
            group, _ = Group.objects.get_or_create(name=target_group_name)
            all_role_groups = Group.objects.filter(
                name__in=["Reader", "Editor", "Journalist"]
            )
            self.groups.remove(*all_role_groups.exclude(id=group.id))
            self.groups.add(group)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Article(models.Model):
    """News articles authored by independent journalists or affiliated with a
    publisher[cite: 4]."""

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="articles",
        limit_choices_to={"role": "JOURNALIST"},
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Approved" if self.approved else "Pending"
        return f"{self.title} [{status}]"


class Newsletter(models.Model):
    """Curated collections of articles created by journalists[cite: 4]."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="newsletters",
        limit_choices_to={"role": "JOURNALIST"},
    )
    articles = models.ManyToManyField(
        Article, related_name="newsletters", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
