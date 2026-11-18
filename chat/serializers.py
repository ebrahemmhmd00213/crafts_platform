from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender_name', 'content', 'is_read', 'created_at']
        read_only_fields = ['sender_name', 'is_read', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    technician_name = serializers.CharField(source='technician.username', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'order', 'customer_name', 'technician_name',
            'last_message', 'unread_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        return MessageSerializer(last).data if last else None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()