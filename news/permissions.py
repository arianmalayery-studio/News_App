"""Custom Django REST Framework permissions for role-based access control.

Defines permission classes restricting API actions by Journalist,
Editor, and article authorship roles.
"""

from rest_framework import permissions

from .models import CustomUser


class IsJournalist(permissions.BasePermission):
    """Permits access only to users with the Journalist role[cite: 5, 7]."""

    def has_permission(self, request, view):
        """Allow access if user is a journalist or superuser."""
        return request.user.is_authenticated and (
            request.user.role == CustomUser.Role.JOURNALIST
            or request.user.is_superuser
        )


class IsEditor(permissions.BasePermission):
    """Permits access only to users with the Editor role[cite: 5, 7]."""

    def has_permission(self, request, view):
        """Allow access if user is an editor or superuser."""
        return request.user.is_authenticated and (
            request.user.role == CustomUser.Role.EDITOR
            or request.user.is_superuser
        )


class IsEditorOrAuthorOrReadOnly(permissions.BasePermission):
    """Control article access by user role and authorship.

    - Safe methods (GET, HEAD, OPTIONS): open to authenticated users.
    - POST: Only journalists can create articles.
    - PUT, PATCH, DELETE: Only Editors or the original authoring
      Journalist.
    """

    def has_permission(self, request, view):
        """Check view-level permissions based on role and HTTP method."""
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "POST":
            return (
                request.user.role == CustomUser.Role.JOURNALIST
                or request.user.is_superuser
            )
        return True

    def has_object_permission(self, request, view, obj):
        """Allow edits by editors, superusers, or the article author."""
        if request.method in permissions.SAFE_METHODS:
            return True
        # Editors and superusers have full write permissions
        if (
            request.user.role == CustomUser.Role.EDITOR
            or request.user.is_superuser
        ):
            return True
        # Journalists can only modify/delete their own articles
        return obj.author == request.user
