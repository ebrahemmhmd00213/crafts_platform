# orders/api.py
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
from .serializers import ServiceOrderSerializer
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
        if self.action == 'withdraw':
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
        # استثناء الطلبات المحذوفة منطقيًا
        base = ServiceOrder.objects.filter(is_deleted=False).select_related(
            'customer', 'technician', 'service_type'
        ).order_by('-created_at')

        if user.role == User.Role.CUSTOMER:
            return base.filter(customer=user)

        if user.role == User.Role.TECHNICIAN:
            try:
                profile = user.tech_profile
            except User.tech_profile.RelatedObjectDoesNotExist:
                return base.none()

            # في retrieve/start/complete/withdraw: الطلبات المُعيَّنة له فقط
            if self.action in ['retrieve', 'start', 'complete', 'withdraw']:
                return base.filter(technician=user)

            # في list: الطلبات المتاحة + المُعيَّنة له
            return base.filter(
                Q(
                    status__in=['open', 'offers_received'],
                    service_type_id=profile.service_type_id,   # ✅ FK
                )
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

            tech_ids = [t.user_id for t in find_nearby_technicians(order)]

            if tech_ids:
                transaction.on_commit(
                    lambda: notify_nearby_technicians.delay(order.id, tech_ids)
                )

        logger.info(
            f"Order {order.id} created by user {self.request.user.id}, "
            f"notifying {len(tech_ids)} technicians"
        )

    # ─────────────────────────────────────────────
    # ✅ إصلاح الخطأ 4: حذف منطقي فقط
    # ─────────────────────────────────────────────
    def destroy(self, request, *args, **kwargs):
        order = self.get_object()

        if order.status in [ServiceOrder.Status.COMPLETED, ServiceOrder.Status.REVIEWED]:
            return Response(
                {'error': 'لا يمكن حذف طلب مكتمل أو مُقيَّم'},
                status=400,
            )
        if order.status == ServiceOrder.Status.IN_PROGRESS:
            return Response(
                {'error': 'لا يمكن حذف طلب قيد التنفيذ'},
                status=400,
            )

        order.is_deleted = True
        order.deleted_at = timezone.now()
        order.save(update_fields=['is_deleted', 'deleted_at'])

        logger.info(f"Order {order.id} soft-deleted by user {request.user.id}")
        return Response(status=204)

    # ─────────────────────────────────────────────
    # الفني يبدأ التنفيذ
    # ─────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
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
    # ✅ إصلاح الخطأ 6: السعر = سعر العرض المقبول (لا يُدخله الفني)
    # ─────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()

        if order.status != ServiceOrder.Status.IN_PROGRESS:
            return Response(
                {'error': f'لا يمكن إكمال طلب في الحالة {order.status}'},
                status=400,
            )

        accepted_offer = order.offers.filter(is_accepted=True).first()
        if not accepted_offer:
            return Response(
                {'error': 'لا يوجد عرض مقبول لهذا الطلب'},
                status=400,
            )

        # ✅ السعر النهائي = سعر العرض المقبول (خادم يحدده، لا الفني)
        order.final_price = accepted_offer.price
        order.status = ServiceOrder.Status.COMPLETED
        order.completed_at = timezone.now()
        order.save(update_fields=['final_price', 'status', 'completed_at'])

        # احتساب العمولة تلقائيًا
        from commissions.services import create_commission
        try:
            create_commission(order)
        except Exception as e:
            logger.error(f"Commission failed for order {order.id}: {e}")

        logger.info(
            f"Order {order.id} completed by technician {request.user.id} "
            f"with price {order.final_price}"
        )
        return Response(ServiceOrderSerializer(order).data)

    # ─────────────────────────────────────────────
    # العميل يلغي الطلب
    # ─────────────────────────────────────────────
    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated, IsCustomer, IsOrderOwner])
    def cancel(self, request, pk=None):
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

    # ─────────────────────────────────────────────
    # ✅ إضافة: الفني ينسحب من الطلب
    # ─────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        order = self.get_object()

        if order.status != ServiceOrder.Status.ASSIGNED:
            return Response(
                {'error': 'لا يمكن الانسحاب إلا من طلب مُعيَّن'},
                status=400,
            )

        # إلغاء قبول العرض
        order.offers.filter(is_accepted=True).update(is_accepted=False)

        order.technician = None
        order.status = ServiceOrder.Status.OFFERS_RECEIVED
        order.final_price = None
        order.save(update_fields=['technician', 'status', 'final_price'])

        logger.info(f"Technician {request.user.id} withdrew from order {order.id}")
        return Response(ServiceOrderSerializer(order).data)