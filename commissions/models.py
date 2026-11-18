from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from orders.models import ServiceOrder

class MainModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta :

        abstract =True


class Commission(MainModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'قيد التحصيل'
        PAID = 'paid', 'مدفوعة'
        CANCELLED = 'cancelled', 'ملغاة'

    order = models.OneToOneField(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name='commission',
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,   # ← لا تحذف سجلات مالية
        related_name='commissions',
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING,
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['technician', 'status']),
        ]

    def __str__(self):
        return f'عمولة طلب #{self.order_id} - {self.amount} ({self.status})'

    @property
    def is_paid(self):
        return self.status == self.Status.PAID