import logging
import firebase_admin
from firebase_admin import messaging

logger = logging.getLogger(__name__)


def _send(user, title, body, data=None):
    """
    إرسال إشعار FCM لمستخدم (إن كان لديه token).
    - يتحقق من تهيئة Firebase.
    - يتجاهل المستخدمين بلا fcm_token.
    - يسجّل الأخطاء دون إفشال العملية.
    """
    # 1) التحقق من تهيئة Firebase
    if not firebase_admin._apps:
        logger.warning("[FCM] Firebase not initialized — skipping")
        return False

    # 2) التحقق من وجود token
    if not user or not getattr(user, 'fcm_token', ''):
        logger.info(f"[FCM] User {getattr(user, 'id', '?')} has no fcm_token")
        return False

    # 3) الإرسال
    try:
        messaging.send(messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=user.fcm_token,
        ))
        logger.info(f"[FCM] Sent to user {user.id}: {title}")
        return True
    except Exception as e:
        logger.error(f"[FCM] Failed for user {user.id}: {e}")
        return False


# ─────────────────────────────────────────────
# دوال الإشعارات حسب الحدث
# ─────────────────────────────────────────────

def notify_offer_accepted(order):
    """إشعار الفني عند قبول عرضه."""
    if not order.technician_id:
        return
    _send(
        order.technician,
        title='تم قبول عرضك',
        body=f'قبل العميل عرضك على الطلب #{order.id}',
        data={'order_id': str(order.id), 'type': 'offer_accepted'},
    )


def notify_order_started(order):
    """إشعار العميل عند بدء الفني."""
    _send(
        order.customer,
        title='بدأ الفني العمل',
        body=f'بدأ الفني تنفيذ الطلب #{order.id}',
        data={'order_id': str(order.id), 'type': 'order_started'},
    )


def notify_order_completed(order):
    """إشعار العميل عند إكمال الطلب."""
    _send(
        order.customer,
        title='اكتمل الطلب',
        body=f'اكتمل الطلب #{order.id} — السعر: {order.final_price}',
        data={'order_id': str(order.id), 'type': 'order_completed'},
    )


def notify_order_cancelled(order):
    """إشعار الفني عند إلغاء العميل."""
    if not order.technician_id:
        return
    _send(
        order.technician,
        title='تم إلغاء الطلب',
        body=f'ألغى العميل الطلب #{order.id}',
        data={'order_id': str(order.id), 'type': 'order_cancelled'},
    )