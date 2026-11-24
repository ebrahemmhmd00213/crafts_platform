from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User
from .serializers import (
    RegisterSerializer, TechnicianProfileSerializer,
    VerifyOTPSerializer, ResendOTPSerializer,UserProfileSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
)
from .services import verify_otp, generate_otp, send_otp_sms , request_password_reset, verify_otp


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class TechnicianProfileView(generics.CreateAPIView):
    serializer_class = TechnicianProfileSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        ok, message = verify_otp(s.validated_data['phone'], s.validated_data['code'])
        if not ok:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone=s.validated_data['phone'])
            user.is_phone_verified = True
            user.save(update_fields=['is_phone_verified'])
        except User.DoesNotExist:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': 'verified', 'message': message})


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = ResendOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        phone = s.validated_data['phone']
        if not User.objects.filter(phone=phone).exists():
            return Response({'error': 'لا يوجد مستخدم بهذا الرقم'}, status=status.HTTP_404_NOT_FOUND)

        otp = generate_otp(phone)
        if not send_otp_sms(phone, otp.code):
            return Response({'error': 'فشل إرسال الرمز'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({'status': 'sent'})


    







class ProfileView(generics.RetrieveUpdateAPIView):
    """عرض/تعديل بروفايل المستخدم الحالي."""
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class PasswordResetRequestView(APIView):
    """بدء إعادة تعيين كلمة المرور (يرسل OTP)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = PasswordResetRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        phone = s.validated_data['phone']
        if not request_password_reset(phone):
            # لأسباب أمنية: لا نكشف إن كان الرقم موجودًا
            return Response({'status': 'sent'})

        return Response({'status': 'sent'})


class PasswordResetConfirmView(APIView):
    """تأكيد إعادة التعيين (OTP + كلمة مرور جديدة)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        phone = s.validated_data['phone']
        code = s.validated_data['code']
        new_password = s.validated_data['new_password']

        # تحقق من OTP
        ok, message = verify_otp(phone, code)
        if not ok:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        # غيّر كلمة المرور
        try:
            user = User.objects.get(phone=phone)
            user.set_password(new_password)
            user.save(update_fields=['password'])
        except User.DoesNotExist:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': 'reset', 'message': 'تم تغيير كلمة المرور بنجاح'})

class RegisterFCMTokenView(APIView):
    """تسجيل/تحديث FCM token للمستخدم."""
    def post(self, request):
        token = request.data.get('fcm_token', '').strip()
        if not token:
            return Response({'error': 'fcm_token مطلوب'}, status=400)

        user = request.user
        user.fcm_token = token
        user.save(update_fields=['fcm_token'])

        return Response({'status': 'registered'})


