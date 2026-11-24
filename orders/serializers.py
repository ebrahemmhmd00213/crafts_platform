# orders/serializers.py
from rest_framework import serializers
from .models import ServiceOrder, OrderImage


class OrderImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderImage
        fields = ['id', 'image']


class ServiceOrderSerializer(serializers.ModelSerializer):
    service_type_name = serializers.CharField(source='service_type.name', read_only=True)
    images = OrderImageSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceOrder
        fields = [
            'id', 'title', 'description', 'service_type', 'service_type_name',
            'latitude', 'longitude', 'status',
            'customer', 'technician', 'final_price',
            'created_at', 'images',
        
        ]
        read_only_fields = [      
            'customer', 'technician', 'status',
            'final_price', 'created_at',
        ]

    def validate_service_type(self, value):
        if not value.is_active:
            raise serializers.ValidationError('نوع الخدمة غير متاح')
        return value


class CompleteOrderSerializer(serializers.Serializer):
    """Serializer للتحقق من final_price عند إكمال الطلب."""
    final_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0
    )