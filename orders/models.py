from django.conf import settings
from django.db import models
from accounts.models import User



class MainModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta :

        abstract =True


class ServiceOrder(MainModel):
    class Status(models.TextChoices):
        OPEN = 'open', 'مفتوح'
        OFFERS_RECEIVED = 'offers_received', 'عروض مقدمة'
        ASSIGNED = 'assigned', 'مُعيَّن'
        IN_PROGRESS = 'in_progress', 'قيد التنفيذ'
        COMPLETED = 'completed', 'مكتمل'
        REVIEWED = 'reviewed', 'مقيم'
        CANCELLED = 'cancelled', 'ملغى'

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='assigned_orders')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    service_type = models.ForeignKey('accounts.ServiceType', on_delete=models.PROTECT, related_name='orders')
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

class OrderImage(MainModel):
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='orders/')