# orders/tasks.py
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def notify_nearby_technicians(self, order_id, technician_user_ids):
    """إرسال إشعار للفنيين القريبين — يعمل في الخلفية."""
    from orders.models import ServiceOrder
    from accounts.models import User
    from orders.notifications import send_push_notification

    try:
        order = ServiceOrder.objects.get(id=order_id)
    except ServiceOrder.DoesNotExist:
        logger.warning(f"Order {order_id} not found for notification")
        return

    technicians = User.objects.filter(id__in=technician_user_ids)
    for tech in technicians:
        try:
            send_push_notification(
                user=tech,
                title="طلب جديد قريب منك",
                body=f"{order.service_type}: {order.title}",
                data={'order_id': order.id},
            )
        except Exception as exc:
            logger.error(f"Failed to notify user {tech.id}: {exc}")
            # retry اختياري