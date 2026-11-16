# orders/permissions.py
from rest_framework import permissions
from accounts.models import User


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.CUSTOMER
        )


class IsTechnician(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.TECHNICIAN
        )


class IsOrderOwner(permissions.BasePermission):
    """العميل مالك الطلب."""
    def has_object_permission(self, request, view, obj):
        return obj.customer_id == request.user.id


class IsAssignedTechnician(permissions.BasePermission):
    """الفني المُعيَّن للطلب."""
    def has_object_permission(self, request, view, obj):
        return obj.technician_id == request.user.id