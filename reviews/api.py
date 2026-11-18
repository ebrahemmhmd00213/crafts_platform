from django.db import IntegrityError
from rest_framework import viewsets, permissions, serializers
from .models import Review
from .serializers import ReviewSerializer
from .permissions import IsCustomer, IsReviewOwner


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsCustomer()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCustomer(), IsReviewOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        base = Review.objects.select_related('order', 'customer', 'technician')
        if user.role == 'technician':
            return base.filter(technician=user)
        return base.filter(customer=user)

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        try:
            serializer.save(
                customer=self.request.user,
                technician=order.technician,
            )
        except IntegrityError:
            raise serializers.ValidationError('تم تقييم هذا الطلب مسبقاً')