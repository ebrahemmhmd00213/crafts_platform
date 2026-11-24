from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

class MainModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta :

        abstract =True


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'customer'
        TECHNICIAN = 'technician'
        ADMIN = 'admin'

    role = models.CharField(max_length=15, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=20, unique=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    fcm_token = models.CharField(max_length=255, blank=True, default='')
    is_phone_verified = models.BooleanField(default=False)


class ServiceType(MainModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    

    class Meta:
        ordering = ['name']


    def save(self, *args, **kwargs):
            if not self.slug:
                self.slug = slugify(self.name, allow_unicode=True)
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TechnicianProfile(MainModel):
    class Status(models.TextChoices):
        PENDING = 'pending'
        APPROVED = 'approved'
        REJECTED = 'rejected'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tech_profile')
    service_type = models.ForeignKey( ServiceType, on_delete=models.PROTECT, related_name='technicians' )      
    id_document = models.ImageField(upload_to='ids/')
    photo = models.ImageField(upload_to='photos/')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    avg_rating = models.FloatField(default=0)
    avg_response_minutes = models.FloatField(default=60)

    def __str__(self):
        return f'{self.user.username} - {self.service_type}'




class PhoneOTP(MainModel):
    """رمز OTP مؤقت للتحقق من رقم الهاتف."""
    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f'{self.phone} — {self.code}'