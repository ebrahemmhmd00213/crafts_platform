# orders/views.py
import logging

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import UserRateThrottle

from accounts.models import User
from .models import ServiceOrder, OrderImage
from .serializers import ServiceOrderSerializer, CompleteOrderSerializer
from .services import find_nearby_technicians
from .permissions import (
    IsCustomer, IsTechnician, IsOrderOwner, IsAssignedTechnician,
)
from .tasks import notify_nearby_technicians

logger = logging.getLogger(__name__)


class OrderCreateThrottle(UserRateThrottle):
    scope = 'order_create'
    rate = '10/hour'


class ServiceOrderViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceOrderSerializer

    # ─────────────────────────────────────────────
    # الصلاحيات حسب الإجراء
    # ─────────────────────────────────────────────
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsCustomer()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCustomer(), IsOrderOwner()]
        if self.action in ['start', 'complete']:
            return [permissions.IsAuthenticated(), IsTechnician(), IsAssignedTechnician()]
        return [permissions.IsAuthenticated()]

    def get_throttles(self):
        if self.action == 'create':
            return [OrderCreateThrottle()]
        return []

    # ─────────────────────────────────────────────
    # تصفية البيانات حسب الدور والإجراء
    # ─────────────────────────────────────────────
    def get_queryset(self):
        user = self.request.user
        base = ServiceOrder.objects.select_related('customer', 'technician').order_by('-created_at')

        if user.role == User.Role.CUSTOMER:
            return base.filter(customer=user)

        if user.role == User.Role.TECHNICIAN:
            try:
                profile = user.tech_profile
            except User.tech_profile.RelatedObjectDoesNotExist:
                return base.none()
            # في retrieve/start/complete: الطلبات المُعيَّنة له فقط
            if self.action in ['retrieve', 'start', 'complete']:
                return base.filter(technician=user)
            # في list: الطلبات المتاحة + المُعيَّنة له
            return base.filter(
                Q(status__in=['open', 'offers_received'],
                  service_type=user.tech_profile.service_type)
                | Q(technician=user)
            )

        # admin
        return base.all()

    # ─────────────────────────────────────────────
    # إنشاء الطلب (مع الصور والإشعارات)
    # ─────────────────────────────────────────────
    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(customer=self.request.user)

            for img in self.request.FILES.getlist('images'):
                if img.size > 5 * 1024 * 1024:
                    raise ValidationError(f"الصورة {img.name} تتجاوز 5MB")
                if not img.content_type.startswith('image/'):
                    raise ValidationError(f"الملف {img.name} ليس صورة")
                OrderImage.objects.create(order=order, image=img)

            # البحث عن الفنيين داخل الـ transaction (لأننا نحتاج order)
            tech_ids = [t.user_id for t in find_nearby_technicians(order)]

            # الإشعارات بعد commit فقط
            if tech_ids:
                transaction.on_commit(
                    lambda: notify_nearby_technicians.delay(order.id, tech_ids)
                )

        logger.info(
            f"Order {order.id} created by user {self.request.user.id}, "
            f"notifying {len(tech_ids)} technicians"
        )

    def destroy(self, request, *args, **kwargs):
        """منع حذف الطلبات المكتملة أو قيد التنفيذ."""
        order = self.get_object()

        if order.status in [ServiceOrder.Status.COMPLETED,ServiceOrder.Status.REVIEWED,]:
            return Response({'error': 'لا يمكن حذف طلب مكتمل أو مُقيَّم'},status=400,)

        if order.status == ServiceOrder.Status.IN_PROGRESS:
            return Response({'error': 'لا يمكن حذف طلب قيد التنفيذ'},status=400,)

        order.is_deleted = True
        order.deleted_at = timezone.now()
        order.save(update_fields=['is_deleted', 'deleted_at'])
        

        return super().destroy(request, *args, **kwargs), Response(status=204)

    # ─────────────────────────────────────────────
    # الفني يبدأ التنفيذ
    # ─────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """الفني يبدأ تنفيذ الطلب (من assigned إلى in_progress)."""
        order = self.get_object()

        if order.status != ServiceOrder.Status.ASSIGNED:
            return Response(
                {'error': f'لا يمكن البدء من الحالة {order.status}'},
                status=400,
            )

        order.status = ServiceOrder.Status.IN_PROGRESS
        order.started_at = timezone.now()
        order.save(update_fields=['status', 'started_at'])

        logger.info(f"Order {order.id} started by technician {request.user.id}")
        return Response(ServiceOrderSerializer(order).data)

    # ─────────────────────────────────────────────
    # الفني يكمل الطلب ويسجل السعر
    # ─────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """الفني ينهي التنفيذ ويسجل السعر النهائي (دفع نقدي)."""
        order = self.get_object()

        # 1) التحقق من الحالة
        if order.status != ServiceOrder.Status.IN_PROGRESS:
            return Response(
                {'error': f'لا يمكن إكمال طلب في الحالة {order.status}'},
                status=400,
            )

        # 2) التحقق من صحة البيانات
        s = CompleteOrderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        price = s.validated_data['final_price']

        # 3) التحقق من وجود عرض مقبول
        accepted_offer = order.offers.filter(is_accepted=True).first()
        if not accepted_offer:
            return Response(
                {'error': 'لا يوجد عرض مقبول لهذا الطلب'},
                status=400,
            )

        # 4) منع السعر غير المنطقي (أقل من 50% من العرض المقبول)
        from decimal import Decimal
        if price <= 0:
            return Response(
                {'error': 'السعر النهائي يجب أن يكون أكبر من صفر'},
                status=400,
            )
        if price < (accepted_offer.price * Decimal('0.5')):
            return Response(
                {'error': 'السعر النهائي أقل من الحد المسموح مقارنة بالعرض المقبول'},
                status=400,
            )

        # 5) حفظ الطلب
        order.final_price = price
        order.status = ServiceOrder.Status.COMPLETED
        order.completed_at = timezone.now()
        order.save(update_fields=['final_price', 'status', 'completed_at'])

        # 6) احتساب العمولة تلقائياً (على الخادم)
        from commissions.services import create_commission
        try:
            create_commission(order)
        except ValueError as e:
            logger.error(f"Commission failed for order {order.id}: {e}")

        logger.info(
            f"Order {order.id} completed by technician {request.user.id} "
            f"with price {order.final_price}"
        )
        return Response(ServiceOrderSerializer(order).data)

    # ─────────────────────────────────────────────
    # العميل يلغي الطلب (اختياري لكن مفيد)
    # ─────────────────────────────────────────────
    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated, IsCustomer, IsOrderOwner])
    def cancel(self, request, pk=None):
        """العميل يلغي طلبه (فقط قبل البدء بالتنفيذ)."""
        order = self.get_object()

        if order.status not in [
            ServiceOrder.Status.OPEN,
            ServiceOrder.Status.OFFERS_RECEIVED,
            ServiceOrder.Status.ASSIGNED,
        ]:
            return Response(
                {'error': f'لا يمكن الإلغاء من الحالة {order.status}'},
                status=400,
            )

        order.status = ServiceOrder.Status.CANCELLED
        order.save(update_fields=['status'])

        logger.info(f"Order {order.id} cancelled by customer {request.user.id}")
        return Response(ServiceOrderSerializer(order).data)