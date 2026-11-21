from rest_framework import serializers
from .models import Offer


class OfferSerializer(serializers.ModelSerializer):
    technician_name = serializers.CharField(
        source='technician.username', read_only=True
    )
    technician_rating = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'order', 'technician_name', 'technician_rating',
            'price', 'estimated_hours', 'message',
            'is_accepted', 'is_locked', 'created_at',
        ]
        read_only_fields = ['is_accepted', 'is_locked', 'created_at']

    def get_technician_rating(self, obj):
        if not obj.technician or not hasattr(obj.technician, 'tech_profile'):
            return None
        return obj.technician.tech_profile.avg_rating

    def validate_order(self, order):
        user = self.context['request'].user

        if user.role != 'technician':
            raise serializers.ValidationError('فقط الفنيون يمكنهم تقديم عروض')
        if order.customer_id == user.id:
            raise serializers.ValidationError('لا يمكنك تقديم عرض على طلبك')
        if order.status not in ['open', 'offers_received']:
            raise serializers.ValidationError('الطلب لا يستقبل عروضاً حالياً')
        if order.offers.count() >= 5:
            raise serializers.ValidationError('تم الوصول للحد الأقصى (5 عروض)')
        if Offer.objects.filter(order=order, technician=user).exists():
            raise serializers.ValidationError('قدمت عرضاً على هذا الطلب مسبقاً')

        return order