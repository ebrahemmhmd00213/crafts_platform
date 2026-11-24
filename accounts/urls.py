from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView,TokenBlacklistView
from .api import (
    RegisterView,
      TechnicianProfileView,
      VerifyOTPView,
      ResendOTPView,
      PasswordResetRequestView,
      PasswordResetConfirmView,
      ProfileView,
      RegisterFCMTokenView,
)
urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('logout/', TokenBlacklistView.as_view(), name='logout'),
    path('technician-profile/', TechnicianProfileView.as_view()),
    path('verify-otp/', VerifyOTPView.as_view()),       
    path('resend-otp/', ResendOTPView.as_view()),
    path('password-reset/request/', PasswordResetRequestView.as_view()),   
    path('password-reset/confirm/', PasswordResetConfirmView.as_view()),
    path('profile/', ProfileView.as_view()),
    path('fcm-token/', RegisterFCMTokenView.as_view()),
]