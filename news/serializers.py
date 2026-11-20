"""Django REST Framework serializers for the news application API.

Provides serialization and validation for Publisher, CustomUser,
Article, Newsletter, and approved-article webhook log payloads.
"""

from rest_framework import serializers

from .models import CustomUser, Publisher, Article, Newsletter


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer for Publisher entities[cite: 4, 8]."""

    class Meta:
        """Metadata options for PublisherSerializer."""

        model = Publisher
        fields = ["id", "name", "description", "created_at"]


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for User profiles, roles, and subscriptions[cite: 6, 8]."""

    class Meta:
        """Metadata options for CustomUserSerializer."""

        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "role",
            "subscribed_publishers",
            "subscribed_journalists",
        ]
        read_only_fields = ["role"]


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for news articles[cite: 4, 8]."""

    author_username = serializers.ReadOnlyField(source="author.username")
    publisher_name = serializers.ReadOnlyField(source="publisher.name")

    class Meta:
        """Metadata options for ArticleSerializer."""

        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "author_username",
            "publisher",
            "publisher_name",
            "approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "author",
            "approved",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Create an unapproved article authored by the current user."""
        # Automatically assign the logged-in journalist as author
        validated_data["author"] = self.context["request"].user
        validated_data["approved"] = False
        return super().create(validated_data)


class NewsletterSerializer(serializers.ModelSerializer):
    """Serializer for curated newsletters[cite: 4, 8]."""

    author_username = serializers.ReadOnlyField(source="author.username")

    class Meta:
        """Metadata options for NewsletterSerializer."""

        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "author",
            "author_username",
            "articles",
            "created_at",
        ]
        read_only_fields = ["author", "created_at"]

    def create(self, validated_data):
        """Create a newsletter authored by the current user."""
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class ApprovedArticleLogSerializer(serializers.Serializer):
    """Serializer for approved article webhook payloads.

    Validates external syndication simulation payloads[cite: 6, 7].
    """

    article_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    author = serializers.CharField(max_length=150)
    publisher = serializers.CharField(
        max_length=255, allow_null=True, required=False
    )
    approved_at = serializers.DateTimeField()
