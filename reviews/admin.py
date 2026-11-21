from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'customer', 'technician', 'stars', 'created_at']
    list_filter = ['stars']
    search_fields = ['order__title', 'customer__username', 'technician__username']