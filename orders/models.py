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
        CANCELLED = 'cancelled', 'ملغى'

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # ← سلسلة نصية 'accounts.User'
        on_delete=models.CASCADE,
    )
    technician = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_orders',
        limit_choices_to={'role': 'technician'},)
    
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    service_type = models.CharField(max_length=50)
    

    class Meta:
        ordering = ['-created_at']


class OrderImage(MainModel):
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='orders/')