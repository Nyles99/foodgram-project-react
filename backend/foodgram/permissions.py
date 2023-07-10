from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    '''Доступ имеет только админ'''

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_staff)


class IsAuthorOrReadOnly(permissions.BasePermission):
    '''Доступ имеет только автор'''

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated
                and obj.author == request.user)
