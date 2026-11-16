# orders/serializers.py
from rest_framework import serializers
from .models import ServiceOrder, OrderImage


class OrderImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderImage
        fields = ['id', 'image']


class ServiceOrderSerializer(serializers.ModelSerializer):
    images = OrderImageSerializer(many=True, read_only=True)   # للعرض فقط

    class Meta:
        model = ServiceOrder
        fields = [
            'id', 'title', 'description', 'service_type',
            'latitude', 'longitude', 'status',
            'customer', 'technician', 'final_price',
            'created_at', 'images',
        ]
        read_only_fields = [
            'customer', 'technician', 'status',
            'final_price', 'created_at',
        ]


class CompleteOrderSerializer(serializers.Serializer):
    """Serializer للتحقق من final_price عند إكمال الطلب."""
    final_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0
    )