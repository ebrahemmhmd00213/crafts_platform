from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'customer', 'technician', 'created_at', 'updated_at']
    search_fields = ['order__title', 'customer__username', 'technician__username']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['content', 'sender__username']