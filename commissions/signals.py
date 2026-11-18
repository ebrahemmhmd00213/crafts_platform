from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

from orders.models import ServiceOrder
from offers.models import Offer
from .models import Commission


@receiver(post_save, sender=ServiceOrder)
def handle_commission(sender, instance, **kwargs):
    
    if instance.status == ServiceOrder.Status.COMPLETED and instance.final_price:
        if Commission.objects.filter(order=instance).exists():
            return   

        offer = instance.offers.filter(is_accepted=True).select_related('technician').first()
        if not offer or not offer.technician_id:
            return   

        Commission.objects.create(
            order=instance,
            technician=offer.technician,
            amount=instance.final_price * settings.COMMISSION_RATE,
        )

    
    elif instance.status == ServiceOrder.Status.CANCELLED:
        Commission.objects.filter(order=instance).update(
            status=Commission.Status.CANCELLED,
        )