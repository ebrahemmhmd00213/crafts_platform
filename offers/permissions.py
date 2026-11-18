# permissions.py
# offers/permissions.py
from rest_framework import permissions
from accounts.models import User


class IsCustomer(permissions.BasePermission):
    """المستخدم عميل."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.CUSTOMER
        )


class IsTechnician(permissions.BasePermission):
    """المستخدم فني."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.TECHNICIAN
        )


class IsOfferOwner(permissions.BasePermission):
    """الفني مالك العرض (الذي قدّمه)."""
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'technician_id', None) == request.user.id


class IsOfferOrderOwner(permissions.BasePermission):
    """العميل مالك الطلب المرتبط بالعرض."""
    def has_object_permission(self, request, view, obj):
        return getattr(getattr(obj, 'order', None), 'customer_id', None) == request.user.id