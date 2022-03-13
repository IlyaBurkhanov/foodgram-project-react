from rest_framework import permissions


class UserPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated or view.action != 'retrieve'


class RecipesPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
                request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
