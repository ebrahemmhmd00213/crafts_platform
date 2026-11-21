from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'technician', 'price', 'estimated_hours', 'is_accepted', 'is_locked', 'created_at']
    list_filter = ['is_accepted', 'is_locked']
    search_fields = ['order__title', 'technician__username']