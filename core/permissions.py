from rest_framework import permissions

class IsAuthenticated(permissions.BasePermission):
    """
    Allow access only to authenticated users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsOwner(permissions.BasePermission):
    """
    Allow access only to the owner of the object.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user owns the object
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
