from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from .models import Article, CustomUser
from .serializers import (
    ArticleSerializer,
    ApprovedArticleLogSerializer,
)
from .permissions import IsEditorOrAuthorOrReadOnly


class ArticleViewSet(viewsets.ModelViewSet):
    """Handles CRUD operations for articles per user role and
    subscriptions[cite: 7]."""

    serializer_class = ArticleSerializer
    permission_classes = [IsEditorOrAuthorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        # Editors and Superusers can view all articles (approved and
        # unapproved)[cite: 5, 7]
        if user.is_authenticated and (
            user.role == CustomUser.Role.EDITOR or user.is_superuser
        ):
            return Article.objects.all().order_by("-created_at")
        # Journalists can see their own draft articles + all approved
        # articles[cite: 5]
        if user.is_authenticated and user.role == CustomUser.Role.JOURNALIST:
            return Article.objects.filter(
                Q(approved=True) | Q(author=user)
            ).order_by("-created_at")
        # Readers and standard clients only see approved articles[cite: 7]
        return Article.objects.filter(approved=True).order_by("-created_at")

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def subscribed(self, request):
        """GET /api/articles/subscribed/: Return articles matching reader's
        subscriptions[cite: 7]."""
        user = request.user
        if user.role != CustomUser.Role.READER and not user.is_superuser:
            return Response(
                {"detail": "Only readers have subscribed article feeds."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscribed_publishers = user.subscribed_publishers.all()
        subscribed_journalists = user.subscribed_journalists.all()

        articles = (
            Article.objects.filter(approved=True)
            .filter(
                Q(publisher__in=subscribed_publishers)
                | Q(author__in=subscribed_journalists)
            )
            .distinct()
            .order_by("-created_at")
        )

        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def approved_article_webhook(request):
    """POST /api/approved/: Internal endpoint logging article approvals
    triggered by signal[cite: 6, 7]."""
    serializer = ApprovedArticleLogSerializer(data=request.data)
    if serializer.is_valid():
        # Logged to console / response
        data = serializer.validated_data
        print(f"[API APPROVED LOG] Article ID {
            data['article_id']} ('{
            data['title']}') approved.")
        return Response(
            {"status": "logged", "article_id": data["article_id"]},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
