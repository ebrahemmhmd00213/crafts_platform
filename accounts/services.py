import random
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from .models import PhoneOTP

logger = logging.getLogger(__name__)


def _get_twilio_client():
    """إنشاء عميل Twilio (أو None إذا لم تُضبط الإعدادات)."""
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    if not sid or not token:
        return None
    return Client(sid, token)


def generate_otp(phone: str) -> PhoneOTP:
    """توليد رمز OTP جديد لرقم الهاتف (يلغي أي رموز قديمة)."""
    PhoneOTP.objects.filter(phone=phone, is_used=False).update(is_used=True)

    code = f"{random.randint(0, 999999):06d}"
    expires_at = timezone.now() + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 5))

    return PhoneOTP.objects.create(
        phone=phone,
        code=code,
        expires_at=expires_at,
    )


def send_otp_sms(phone: str, code: str) -> bool:
    """إرسال الرمز عبر SMS. يُرجع True عند النجاح."""
    client = _get_twilio_client()
    if not client:
        logger.warning(f"[OTP] Twilio not configured. Code for {phone}: {code}")
        return True   # في التطوير: نعتبره نجاحًا

    try:
        client.messages.create(
            body=f"رمز التحقق الخاص بك هو: {code}\nصالح لمدة {getattr(settings, 'OTP_EXPIRY_MINUTES', 5)} دقائق.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone,
        )
        logger.info(f"[OTP] SMS sent to {phone}")
        return True
    except TwilioRestException as e:
        logger.error(f"[OTP] Twilio error for {phone}: {e}")
        return False


def verify_otp(phone: str, code: str) -> tuple[bool, str]:
    """التحقق من الرمز. يُرجع (نجاح, رسالة)."""
    max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)

    otp = PhoneOTP.objects.filter(phone=phone, is_used=False).order_by('-created_at').first()
    if not otp:
        return False, 'لا يوجد رمز تحقق لهذا الرقم. اطلب رمزًا جديدًا.'

    if not otp.is_valid():
        return False, 'انتهت صلاحية الرمز. اطلب رمزًا جديدًا.'

    if otp.attempts >= max_attempts:
        otp.is_used = True
        otp.save(update_fields=['is_used'])
        return False, 'تجاوزت عدد المحاولات. اطلب رمزًا جديدًا.'

    if otp.code != code:
        otp.attempts += 1
        otp.save(update_fields=['attempts'])
        return False, f'الرمز غير صحيح. المحاولات المتبقية: {max_attempts - otp.attempts}'

    otp.is_used = True
    otp.save(update_fields=['is_used'])
    return True, 'تم التحقق بنجاح.'





def send_password_reset_sms(phone: str, code: str) -> bool:
    """إرسال رمز إعادة تعيين كلمة المرور عبر SMS."""
    client = _get_twilio_client()
    if not client:
        logger.warning(f"[RESET] Twilio not configured. Code for {phone}: {code}")
        return True

    try:
        client.messages.create(
            body=f"رمز إعادة تعيين كلمة المرور: {code}\nصالح لمدة 5 دقائق.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone,
        )
        return True
    except TwilioRestException as e:
        logger.error(f"[RESET] Twilio error for {phone}: {e}")
        return False


def request_password_reset(phone: str) -> bool:
    """بدء إعادة تعيين كلمة المرور (يولّد OTP ويرسله)."""
    from accounts.models import User
    if not User.objects.filter(phone=phone).exists():
        return False

    otp = generate_otp(phone)
    return send_password_reset_sms(phone, otp.code)
