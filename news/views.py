from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Article, CustomUser, Publisher


def home_view(request):
    """Render the main landing page for the application."""
    return render(request, "news/home.html")


def public_articles_view(request):
    """Display all approved news articles on an HTML page."""
    articles = Article.objects.filter(approved=True).order_by("-created_at")
    return render(request, "news/articles_list.html", {"articles": articles})


def developer_portal_view(request):
    """Render API documentation and Reddit developer links."""
    return render(request, "news/developer_portal.html")


@login_required(login_url="login")
def reader_feed_view(request):
    """Display subscribed news articles for readers and superusers."""
    user = request.user
    if user.role != CustomUser.Role.READER and not user.is_superuser:
        messages.warning(
            request, "Subscribed feeds are dedicated to Reader accounts."
        )
        return redirect("home")

    articles = (
        Article.objects.filter(approved=True)
        .filter(
            Q(publisher__in=user.subscribed_publishers.all())
            | Q(author__in=user.subscribed_journalists.all())
        )
        .distinct()
        .order_by("-created_at")
    )
    return render(request, "news/reader_feed.html", {"articles": articles})


@login_required(login_url="login")
def toggle_author_sub_view(request, author_id):
    """Allow readers to toggle subscription directly from article cards."""
    user = request.user
    if user.role != CustomUser.Role.READER and not user.is_superuser:
        messages.warning(request, "Only readers can subscribe to authors.")
        return redirect("public_articles")

    author = get_object_or_404(
        CustomUser, id=author_id, role=CustomUser.Role.JOURNALIST
    )
    if author in user.subscribed_journalists.all():
        user.subscribed_journalists.remove(author)
        messages.info(request, f"Unsubscribed from {author.username}.")
    else:
        user.subscribed_journalists.add(author)
        messages.success(request, f"Subscribed to {author.username}!")

    next_page = request.GET.get("next")
    if next_page == "feed":
        return redirect("reader_feed")
    return redirect("public_articles")


@login_required(login_url="login")
def manage_subscriptions_view(request):
    """Enable readers to manage subscriptions with checkboxes."""
    user = request.user
    if user.role != CustomUser.Role.READER and not user.is_superuser:
        messages.warning(
            request, "Only readers have customizable subscriptions."
        )
        return redirect("home")

    if request.method == "POST":
        selected_journalists = request.POST.getlist("journalists")
        selected_publishers = request.POST.getlist("publishers")

        user.subscribed_journalists.set(selected_journalists)
        user.subscribed_publishers.set(selected_publishers)
        messages.success(request, "Subscriptions successfully updated!")
        return redirect("reader_feed")

    journalists = CustomUser.objects.filter(
        role=CustomUser.Role.JOURNALIST, is_active=True
    )
    publishers = Publisher.objects.all()
    context = {
        "journalists": journalists,
        "publishers": publishers,
    }
    return render(request, "news/manage_subscriptions.html", context)


@login_required(login_url="login")
def journalist_desk_view(request):
    """Allow journalists to submit articles for editorial review."""
    user = request.user
    if user.role != CustomUser.Role.JOURNALIST and not user.is_superuser:
        messages.error(request, "Only journalists can access this desk.")
        return redirect("home")

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        pub_id = request.POST.get("publisher")

        pub = Publisher.objects.filter(id=pub_id).first() if pub_id else None
        Article.objects.create(
            title=title,
            content=content,
            author=user,
            publisher=pub,
            approved=False,
        )
        messages.success(
            request, "Article submitted! It is now pending editor approval."
        )
        return redirect("journalist_desk")

    my_articles = Article.objects.filter(author=user).order_by("-created_at")
    publishers = Publisher.objects.all()
    context = {
        "my_articles": my_articles,
        "publishers": publishers,
    }
    return render(request, "news/journalist_desk.html", context)


def register_view(request):
    """Register users; hold staff roles pending administrator approval."""
    if request.method == "POST":
        uname = request.POST.get("username")
        email = request.POST.get("email")
        pwd = request.POST.get("password")
        role = request.POST.get("role", CustomUser.Role.READER)

        if CustomUser.objects.filter(username=uname).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "news/register.html")

        is_staff_role = role in [
            CustomUser.Role.JOURNALIST,
            CustomUser.Role.EDITOR,
        ]
        is_active = not is_staff_role

        user = CustomUser.objects.create_user(
            username=uname,
            email=email,
            password=pwd,
            role=role,
            is_active=is_active,
            is_staff=is_staff_role,
        )

        if is_staff_role:
            return render(
                request,
                "news/pending_approval_notice.html",
                {"username": uname, "role_display": user.get_role_display()},
            )

        login(request, user)
        messages.success(request, f"Welcome to News App, {uname}!")
        return redirect("home")

    return render(request, "news/register.html")


def login_view(request):
    """Handle user authentication with inactive staff feedback."""
    if request.method == "POST":
        uname = request.POST.get("username")
        pwd = request.POST.get("password")

        user_check = CustomUser.objects.filter(username=uname).first()
        if (
            user_check
            and not user_check.is_active
            and user_check.check_password(pwd)
        ):
            messages.warning(
                request,
                "Your account is pending administrator approval before login.",
            )
            return render(request, "news/login.html")

        user = authenticate(request, username=uname, password=pwd)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {uname}!")
            return redirect("home")
        messages.error(request, "Invalid username or password.")

    return render(request, "news/login.html")


def logout_view(request):
    """Log out user and redirect to home."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


def is_editor(user):
    """Check if user has Editor role, Editor group, or is superuser."""
    return user.is_authenticated and (
        user.is_superuser
        or user.role == CustomUser.Role.EDITOR
        or user.groups.filter(name="Editor").exists()
    )


@login_required(login_url="login")
@user_passes_test(is_editor, login_url="login")
def editor_dashboard(request):
    """Display pending and approved articles for editors and superusers."""
    pending_articles = Article.objects.filter(approved=False).order_by(
        "-created_at"
    )
    approved_articles = Article.objects.filter(approved=True).order_by(
        "-updated_at"
    )

    context = {
        "pending_articles": pending_articles,
        "approved_articles": approved_articles,
    }
    return render(request, "news/editor_dashboard.html", context)


@login_required(login_url="login")
@user_passes_test(is_editor, login_url="login")
def approve_article(request, article_id):
    """Toggle article approval to True, triggering signal."""
    if request.method == "POST":
        article = get_object_or_404(Article, id=article_id)
        if not article.approved:
            article.approved = True
            article.save()
            messages.success(
                request,
                f"Article '{article.title}' approved and published.",
            )
        else:
            messages.info(
                request, f"Article '{article.title}' was already approved."
            )
    return redirect("editor_dashboard")


@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser, login_url="login")
def pending_users_view(request):
    """List staff accounts awaiting admin activation."""
    pending_users = CustomUser.objects.filter(is_active=False).order_by(
        "-date_joined"
    )
    return render(
        request, "news/pending_users.html", {"pending_users": pending_users}
    )


@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser, login_url="login")
def approve_user_view(request, user_id):
    """Activate a pending user account."""
    if request.method == "POST":
        target_user = get_object_or_404(CustomUser, id=user_id)
        target_user.is_active = True
        target_user.save()
        messages.success(
            request,
            f"User '{target_user.username}' has been approved and activated!",
        )
    return redirect("pending_users")
