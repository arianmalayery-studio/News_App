from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import api_views, views

router = DefaultRouter()
router.register(r"articles", api_views.ArticleViewSet, basename="article")

urlpatterns = [
    # Navigation & General UI
    path("", views.home_view, name="home"),
    path("articles/", views.public_articles_view, name="public_articles"),
    path("feed/", views.reader_feed_view, name="reader_feed"),
    path(
        "author/sub/<int:author_id>/",
        views.toggle_author_sub_view,
        name="toggle_author_sub",
    ),
    path(
        "subscriptions/",
        views.manage_subscriptions_view,
        name="manage_subscriptions",
    ),
    path("desk/", views.journalist_desk_view, name="journalist_desk"),
    path("developer/", views.developer_portal_view, name="developer_portal"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Editorial Dashboard (accessible by editors and superusers)
    path(
        "editor/dashboard/",
        views.editor_dashboard,
        name="editor_dashboard",
    ),
    path(
        "editor/approve/<int:article_id>/",
        views.approve_article,
        name="approve_article",
    ),
    # Admin Staff Approvals
    path("admin-approvals/", views.pending_users_view, name="pending_users"),
    path(
        "admin-approvals/approve/<int:user_id>/",
        views.approve_user_view,
        name="approve_user",
    ),
    # RESTful API Endpoints
    path("api/", include(router.urls)),
    path(
        "api/approved/",
        api_views.approved_article_webhook,
        name="api_approved",
    ),
    path("api/token/", obtain_auth_token, name="api_token"),
]
