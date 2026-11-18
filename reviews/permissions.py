from rest_framework import permissions
from accounts.models import User


class IsCustomer(permissions.BasePermission):
    """المستخدم عميل."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.CUSTOMER
        )


class IsReviewOwner(permissions.BasePermission):
    """العميل صاحب التقييم."""
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'customer_id', None) == request.user.id
    