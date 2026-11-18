from rest_framework import serializers
from .models import Commission


class CommissionSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    technician_name = serializers.CharField(
        source='technician.username', read_only=True
    )

    class Meta:
        model = Commission
        fields = [
            'id', 'order_id', 'technician_name', 'amount',
            'status', 'paid_at', 'created_at',
        ]
        read_only_fields = ['amount', 'status', 'paid_at', 'created_at']