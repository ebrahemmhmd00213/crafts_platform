from django.db import IntegrityError, transaction
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from orders.models import ServiceOrder
from .models import Offer
from .serializers import OfferSerializer
from .permissions import (
    IsCustomer, IsTechnician, IsApprovedTechnician,
    IsOfferOwner, IsOfferOrderOwner,
)


class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer

    def get_permissions(self):
        if self.action == 'create':
            # ✅ نطلب فنيًا معتمدًا وليس أي فني
            return [permissions.IsAuthenticated(), IsApprovedTechnician()]
        if self.action == 'accept':
            return [
                permissions.IsAuthenticated(),
                IsCustomer(),
                IsOfferOrderOwner(),
            ]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [
                permissions.IsAuthenticated(),
                IsTechnician(),
                IsOfferOwner(),
            ]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        base = Offer.objects.select_related('order', 'technician')
        if user.role == 'technician':
            return base.filter(technician=user)
        return base.filter(order__customer=user)

    def perform_create(self, serializer):
        with transaction.atomic():
            order = ServiceOrder.objects.select_for_update().get(
                id=serializer.validated_data['order'].id
            )
            if order.offers.count() >= 5:
                raise serializers.ValidationError('تم الوصول للحد الأقصى (5 عروض)')

            try:
                offer = serializer.save(technician=self.request.user)
            except IntegrityError:
                raise serializers.ValidationError('قدمت عرضاً مسبقاً')

            if order.status == ServiceOrder.Status.OPEN:
                order.status = ServiceOrder.Status.OFFERS_RECEIVED
                order.save(update_fields=['status'])

    # ✅ منع تعديل عرض مقبول أو مقفل
    def update(self, request, *args, **kwargs):
        offer = self.get_object()
        if offer.is_accepted or offer.is_locked:
            return Response(
                {'error': 'لا يمكن تعديل عرض مقبول أو مقفل'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        offer = self.get_object()
        if offer.is_accepted or offer.is_locked:
            return Response(
                {'error': 'لا يمكن تعديل عرض مقبول أو مقفل'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        offer = self.get_object()
        if offer.is_accepted:
            return Response(
                {'error': 'لا يمكن حذف عرض مقبول'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        from chat.models import Conversation
        with transaction.atomic():
            offer = self.get_object()
            offer = Offer.objects.select_for_update().select_related('order').get(pk=offer.pk)
            order = offer.order

            if offer.is_accepted:
                return Response({'error': 'هذا العرض مقبول بالفعل'}, status=400)
            if order.status != ServiceOrder.Status.OFFERS_RECEIVED:
                return Response(
                    {'error': f'لا يمكن القبول من الحالة {order.status}'},
                    status=400,
                )

            order.offers.exclude(id=offer.id).update(is_accepted=False, is_locked=True)

            # ✅ قفل العرض المقبول أيضًا
            offer.is_accepted = True
            offer.is_locked = True
            offer.save(update_fields=['is_accepted', 'is_locked'])

            order.technician = offer.technician
            order.status = ServiceOrder.Status.ASSIGNED
            order.final_price = offer.price
            order.save(update_fields=['technician', 'status', 'final_price'])

            Conversation.objects.get_or_create(
                order=order,
                defaults={
                    'customer': order.customer,
                    'technician': offer.technician,
                },
            )
        from orders.notifications import notify_offer_accepted
        notify_offer_accepted(order)
        return Response({
            'status': 'accepted',
            'order_id': order.id,
            'order_status': order.status,
            'technician_id': order.technician_id,
            'final_price': str(order.final_price),
        })