from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import ServiceOrder
from .models import Commission
from .services import create_commission


@receiver(post_save, sender=ServiceOrder)
def handle_commission(sender, instance, **kwargs):
    """
    عند اكتمال الطلب: أنشئ العمولة عبر create_commission (idempotent).
    عند إلغاء الطلب: ألغِ العمولة إن وُجدت.
    """
    if instance.status == ServiceOrder.Status.COMPLETED and instance.final_price:
        try:
            create_commission(instance)
        except ValueError:
            # لا يوجد عرض مقبول أو سعر — تجاهل بهدوء
            pass

    elif instance.status == ServiceOrder.Status.CANCELLED:
        Commission.objects.filter(order=instance).update(
            status=Commission.Status.CANCELLED,
        )