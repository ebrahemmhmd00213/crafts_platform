from rest_framework import serializers
from .models import User, TechnicianProfile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'password', 'phone', 'role']

    def validate_role(self, value):
        
        if value == User.Role.ADMIN:
            raise serializers.ValidationError('User type not allowed')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)  


class TechnicianProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianProfile
        fields = ['service_type', 'id_document', 'photo', 'status']
        read_only_fields = ['status']   