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
    
    

    

    def validate_phone(self, value):
        """تحقق إضافي من رقم الهاتف."""
        if not value.isdigit():
            raise serializers.ValidationError('رقم الهاتف يجب أن يحتوي على أرقام فقط')
        if len(value) < 10:
            raise serializers.ValidationError('رقم الهاتف قصير جدًا')
        return value

    
    def create(self, validated_data):
        from .services import generate_otp, send_otp_sms

        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_phone_verified = False
        user.save()

        # إرسال OTP
        otp = generate_otp(user.phone)
        send_otp_sms(user.phone, otp.code)

        return user

class TechnicianProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianProfile
        fields = ['service_type', 'id_document', 'photo', 'status']
        read_only_fields = ['status']   


class UserProfileSerializer(serializers.ModelSerializer):
    """بروفايل المستخدم — للقراءة والتعديل."""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'phone',
            'latitude', 'longitude', 'fcm_token',
            'is_phone_verified', 'date_joined', 'last_login',
        ]
        read_only_fields = [
            'id', 'username', 'role', 'phone',
            'is_phone_verified', 'date_joined', 'last_login',
        ]


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6, min_length=6)


class ResendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)




class PasswordResetRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)



