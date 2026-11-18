from rest_framework import serializers
from orders.models import ServiceOrder
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    technician_name = serializers.CharField(source='technician.username', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'order', 'customer_name', 'technician_name',
            'stars', 'comment', 'created_at',
        ]
        read_only_fields = ['created_at']

    def validate_order(self, order):
        user = self.context['request'].user

        if order.status != ServiceOrder.Status.COMPLETED:
            raise serializers.ValidationError('لا يمكن تقييم طلب غير مكتمل')
        if order.customer_id != user.id:
            raise serializers.ValidationError('لا يمكنك تقييم طلب ليس لك')
        if not order.technician_id:
            raise serializers.ValidationError('لا يوجد فني معيّن لهذا الطلب')
        if Review.objects.filter(order=order).exists():
            raise serializers.ValidationError('تم تقييم هذا الطلب مسبقاً')

        return order