from django.contrib import admin
from .models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'technician', 'amount', 'status', 'paid_at', 'created_at']
    list_filter = ['status']
    search_fields = ['order__title', 'technician__username']
    readonly_fields = ['created_at', 'updated_at', 'paid_at']