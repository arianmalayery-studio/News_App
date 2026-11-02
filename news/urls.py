from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views
from . import api_views

router = DefaultRouter()
router.register(r"articles", api_views.ArticleViewSet, basename="article")

urlpatterns = [
    # Template UI Routes
    path("editor/dashboard/", views.editor_dashboard, name="editor_dashboard"),
    path(
        "editor/approve/<int:article_id>/",
        views.approve_article,
        name="approve_article",
    ),
    # RESTful API Endpoints[cite: 7]
    path("api/", include(router.urls)),
    path(
        "api/approved/",
        api_views.approved_article_webhook,
        name="api_approved",
    ),
    path("api/token/", obtain_auth_token, name="api_token"),
]
