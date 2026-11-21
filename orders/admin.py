from django.contrib import admin
from .models import ServiceOrder, OrderImage


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'customer', 'technician',
        'service_type', 'status', 'final_price', 'created_at',
    ]
    list_filter = ['status', 'service_type', 'is_deleted']
    search_fields = ['title', 'description', 'customer__username', 'technician__username']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at', 'deleted_at']


@admin.register(OrderImage)
class OrderImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'image', 'created_at']