from rest_framework import permissions
from accounts.models import User


class IsAdmin(permissions.BasePermission):
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.role == User.Role.ADMIN or request.user.is_staff)
        )


class IsCommissionOwner(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'technician_id', None) == request.user.id