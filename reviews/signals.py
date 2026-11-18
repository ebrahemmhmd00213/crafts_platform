
from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from accounts.models import TechnicianProfile
from orders.models import ServiceOrder
from .models import Review


def _recalc_technician_rating(technician_id):
    """إعادة حساب متوسط تقييم الفني."""
    avg = Review.objects.filter(technician_id=technician_id).aggregate(
        avg=Avg('stars')
    )['avg'] or 0
    TechnicianProfile.objects.filter(user_id=technician_id).update(avg_rating=avg)


@receiver(post_save, sender=Review)
def review_saved(sender, instance, created, **kwargs):
    """عند إنشاء/تحديث تقييم: تحديث حالة الطلب + متوسط الفني."""
    if created:
        instance.order.status = ServiceOrder.Status.REVIEWED
        instance.order.save(update_fields=['status'])
    _recalc_technician_rating(instance.technician_id)


@receiver(post_delete, sender=Review)
def review_deleted(sender, instance, **kwargs):
    instance.order.status = ServiceOrder.Status.COMPLETED
    instance.order.save(update_fields=['status'])
    _recalc_technician_rating(instance.technician_id)