from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from .models import Article, CustomUser


def is_editor(user):
    """Check if the user has an Editor role or belongs to the Editor
    group[cite: 4, 6]."""
    return user.is_authenticated and (
        user.role == CustomUser.Role.EDITOR
        or user.groups.filter(name="Editor").exists()
        or user.is_superuser
    )


@login_required
@user_passes_test(is_editor, login_url="admin:login")
def editor_dashboard(request):
    """Display lists of pending (unapproved) and approved articles for
    editors[cite: 6]."""
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


@login_required
@user_passes_test(is_editor, login_url="admin:login")
def approve_article(request, article_id):
    """Toggle article approval to True, which triggers the approval
    signal[cite: 6]."""
    if request.method == "POST":
        article = get_object_or_404(Article, id=article_id)
        if not article.approved:
            article.approved = True
            article.save()  # Triggers the post_save signal in signals.py
            messages.success(
                request,
                f"Article '{article.title}' has been approved and published.",
            )
        else:
            messages.info(
                request, f"Article '{article.title}' was already approved."
            )
    return redirect("editor_dashboard")
