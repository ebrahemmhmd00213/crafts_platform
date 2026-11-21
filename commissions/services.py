from django.conf import settings
from .models import Commission


def create_commission(order):
    """
    إنشاء عمولة للطلب عند اكتماله. آمن ضد التكرار (idempotent).
    يرفع ValueError إذا كانت البيانات ناقصة.
    """
    if order.final_price is None:
        raise ValueError('لا يوجد سعر نهائي للطلب')

    existing = Commission.objects.filter(order=order).first()
    if existing:
        return existing

    offer = order.offers.filter(is_accepted=True).select_related('technician').first()
    if not offer or not offer.technician_id:
        raise ValueError('لا يوجد فني معيّن للطلب')

    amount = order.final_price * settings.COMMISSION_RATE
    return Commission.objects.create(
        order=order,
        technician=offer.technician,
        amount=amount,
    )