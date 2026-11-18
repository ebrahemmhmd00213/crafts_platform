from django.conf import settings
from django.db import models
from orders.models import ServiceOrder


class MainModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta :

        abstract =True


class Conversation(MainModel):
    """محادثة بين العميل والفني حول طلب معيّن."""
    order = models.OneToOneField(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name='conversation',
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_customer',
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_technician',
    )
    

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['order'], name='one_conversation_per_order'),
        ]

    def __str__(self):
        return f'محادثة طلب #{self.order_id}'


class Message(MainModel):
    """رسالة داخل محادثة."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f'{self.sender.username}: {self.content[:30]}'