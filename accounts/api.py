from rest_framework import generics, permissions
from .models import User
from .serializers import RegisterSerializer, TechnicianProfileSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class TechnicianProfileView(generics.CreateAPIView):
    serializer_class = TechnicianProfileSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)