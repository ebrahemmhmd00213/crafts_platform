from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from orders.models import ServiceOrder


class MainModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Offer(MainModel):
    order = models.ForeignKey(
        ServiceOrder, on_delete=models.CASCADE, related_name='offers'
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,   
        null=True,
        related_name='offers',        
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],   
    )
    estimated_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],  
    )
    message = models.TextField(blank=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'technician'],
                name='one_offer_per_tech',
            ),
            models.UniqueConstraint(
                fields=['order'],
                condition=models.Q(is_accepted=True),
                name='one_accepted_offer_per_order',
            ),
        ]
        indexes = [
            models.Index(fields=['order', 'is_accepted']),
        ]

    def __str__(self):
        tech = self.technician.username if self.technician else 'محذوف'
        return f'{tech} → طلب #{self.order_id} ({self.price})'