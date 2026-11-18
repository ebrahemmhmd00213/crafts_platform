from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from orders.models import ServiceOrder



class MainModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Review(MainModel):
    order = models.OneToOneField(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name='review',
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received',
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(blank=True)
    

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['order'], name='one_review_per_order'),
        ]

    def __str__(self):
        return f'تقييم {self.stars}/5 لطلب #{self.order_id}'