from rest_framework import viewsets, permissions, status
from django.db import models
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsConversationParticipant, IsMessageSenderOrParticipant


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """المحادثات للقراءة فقط — تُنشأ تلقائياً عند قبول العرض."""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsConversationParticipant]

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            models.Q(customer=user) | models.Q(technician=user)
        ).select_related('customer', 'technician', 'order')

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """جلب رسائل محادثة."""
        conversation = self.get_object()
        msgs = conversation.messages.select_related('sender')
        msgs.exclude(sender=request.user).update(is_read=True)
        return Response(MessageSerializer(msgs, many=True).data)


class MessageViewSet(viewsets.ModelViewSet):
    """إرسال/قراءة الرسائل — مع حماية من تعديل/حذف رسائل الآخرين."""
    serializer_class = MessageSerializer

    def get_permissions(self):
        # ✅ الإصلاح: تفعيل IsMessageSenderOrParticipant للتعديل والحذف
        if self.action in ['update', 'partial_update', 'destroy']:
            return [
                permissions.IsAuthenticated(),
                IsMessageSenderOrParticipant(),
            ]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            models.Q(conversation__customer=user)
            | models.Q(conversation__technician=user)
        ).select_related('sender', 'conversation')

    def perform_create(self, serializer):
        conversation = serializer.validated_data['conversation']
        user = self.request.user

        if user.id not in (conversation.customer_id, conversation.technician_id):
            raise serializers.ValidationError('أنت لست طرفاً في هذه المحادثة')

        serializer.save(sender=user)
        conversation.save(update_fields=['updated_at'])