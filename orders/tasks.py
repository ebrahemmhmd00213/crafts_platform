from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def notify_nearby_technicians(order_id, tech_ids):
    """
    إرسال إشعارات FCM للفنيين القريبين.
    - يتحقق من تهيئة Firebase قبل الإرسال.
    - يتجاهل الفنيين بلا fcm_token.
    - يسجّل الأخطاء دون إفشال المهمة.
    """
    # 1) التحقق من تهيئة Firebase
    try:
        import firebase_admin
        from firebase_admin import messaging
    except ImportError:
        logger.warning("[NOTIFY] firebase_admin not installed — skipping push")
        return

    if not firebase_admin._apps:
        logger.warning("[NOTIFY] Firebase not initialized — skipping push")
        return

    # 2) جلب الفنيين الذين لديهم token
    from accounts.models import User
    technicians = User.objects.filter(
        id__in=tech_ids,
        fcm_token__isnull=False,
    ).exclude(fcm_token='')

    # 3) إرسال الإشعارات
    sent = 0
    failed = 0
    for tech in technicians:
        try:
            messaging.send(messaging.Message(
                notification=messaging.Notification(
                    title='طلب خدمة جديد',
                    body=f'يوجد طلب جديد قريب منك (رقم {order_id})',
                ),
                token=tech.fcm_token,
            ))
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f"[NOTIFY] FCM failed for user {tech.id}: {e}")

    logger.info(
        f"[NOTIFY] order={order_id} | sent={sent} | failed={failed} "
        f"| total_techs={technicians.count()}"
    )