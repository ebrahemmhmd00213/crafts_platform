from django.db import IntegrityError, transaction
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from orders.models import ServiceOrder
from .models import Offer
from .serializers import OfferSerializer

from .permissions import (
    IsCustomer, IsTechnician, IsOfferOwner, IsOfferOrderOwner,
)


class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer

    # ─────────────────────────────────────────────
    # الصلاحيات حسب الإجراء
    # ─────────────────────────────────────────────
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsTechnician()]
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

    # ─────────────────────────────────────────────
    # تصفية البيانات حسب الدور
    # ─────────────────────────────────────────────
    def get_queryset(self):
        user = self.request.user
        base = Offer.objects.select_related('order', 'technician')
        if user.role == 'technician':
            return base.filter(technician=user)
        return base.filter(order__customer=user)

    # ─────────────────────────────────────────────
    # إنشاء عرض (فني)
    # ─────────────────────────────────────────────
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

    # ─────────────────────────────────────────────
    # منع حذف عرض مقبول
    # ─────────────────────────────────────────────
    def destroy(self, request, *args, **kwargs):
        offer = self.get_object()
        if offer.is_accepted:
            return Response(
                {'error': 'لا يمكن حذف عرض مقبول'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    # ─────────────────────────────────────────────
    # قبول عرض (عميل)
    # ─────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        from chat.models import Conversation
        with transaction.atomic():
            # get_object() يتحقق من IsOfferOrderOwner تلقائياً
            offer = self.get_object()
            offer = Offer.objects.select_for_update().select_related('order').get(pk=offer.pk)
            order = offer.order

            # التحقق من الحالة (الملكية تحققت في get_object)
            if offer.is_accepted:
                return Response({'error': 'هذا العرض مقبول بالفعل'}, status=400)
            if order.status != ServiceOrder.Status.OFFERS_RECEIVED:
                return Response(
                    {'error': f'لا يمكن القبول من الحالة {order.status}'},
                    status=400,
                )

            # رفض باقي العروض
            order.offers.exclude(id=offer.id).update(is_accepted=False)

            # قبول هذا العرض
            offer.is_accepted = True
            offer.save(update_fields=['is_accepted'])

            # تحديث الطلب وتعيين الفني
            order.technician = offer.technician
            order.status = ServiceOrder.Status.ASSIGNED
            order.final_price = offer.price
            order.save(update_fields=['technician', 'status', 'final_price'])

            # ✅ إنشاء المحادثة (إن لم تكن موجودة)
            Conversation.objects.get_or_create(
                order=order,
                defaults={
                    'customer': order.customer,
                    'technician': offer.technician,
                },
            )

        return Response({
            'status': 'accepted',
            'order_id': order.id,
            'order_status': order.status,
            'technician_id': order.technician_id,
            'final_price': str(order.final_price),
        })