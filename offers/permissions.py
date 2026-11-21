# offers/permissions.py
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


class IsApprovedTechnician(permissions.BasePermission):
    """✅ جديد: الفني معتمد (status=approved) وليس مجرد مسجّل."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role != User.Role.TECHNICIAN:
            return False
        try:
            return request.user.tech_profile.status == 'approved'
        except Exception:
            return False


class IsOfferOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'technician_id', None) == request.user.id


class IsOfferOrderOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(getattr(obj, 'order', None), 'customer_id', None) == request.user.id