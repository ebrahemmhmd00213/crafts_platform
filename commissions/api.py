from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from .models import Commission
from .serializers import CommissionSerializer
from .permissions import IsAdmin, IsCommissionOwner


class CommissionViewSet(viewsets.ReadOnlyModelViewSet):
    """العمولات للقراءة فقط — الإنشاء تلقائي عبر signals."""
    serializer_class = CommissionSerializer

    def get_permissions(self):
        if self.action == 'mark_paid':
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        base = Commission.objects.select_related('order', 'technician')

        
        if user.role == User.Role.TECHNICIAN:
            return base.filter(technician=user)

       
        if user.role == User.Role.ADMIN or user.is_staff:
            return base.all()

        
        return base.none()

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        
        commission = self.get_object()
        if commission.status == Commission.Status.PAID:
            return Response(
                {'error': 'العمولة مدفوعة بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        commission.status = Commission.Status.PAID
        commission.paid_at = timezone.now()
        commission.save(update_fields=['status', 'paid_at'])
        return Response(CommissionSerializer(commission).data)