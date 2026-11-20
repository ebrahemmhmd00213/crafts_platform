from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def notify_nearby_technicians(order_id, tech_ids):
    from accounts.models import User
    from firebase_admin import messaging
    technicians = User.objects.filter(id__in=tech_ids, fcm_token__isnull=False).exclude(fcm_token='')
    for tech in technicians:
        try:
            messaging.send(messaging.Message(
                notification=messaging.Notification(
                    title='طلب خدمة جديد',
                    body=f'يوجد طلب جديد قريب منك (رقم {order_id})',
                ),
                token=tech.fcm_token,
            ))
        except Exception as e:
            logger.error(f"FCM failed for {tech.id}: {e}")
    logger.info(f"Notified {technicians.count()} technicians for order {order_id}")