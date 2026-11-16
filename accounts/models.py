from django.db import models
from django.contrib.auth.models import AbstractUser

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


class TechnicianProfile(MainModel):
    class Status(models.TextChoices):
        PENDING = 'pending'
        APPROVED = 'approved'
        REJECTED = 'rejected'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tech_profile')
    service_type = models.CharField(max_length=50)       
    id_document = models.ImageField(upload_to='ids/')
    photo = models.ImageField(upload_to='photos/')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    avg_rating = models.FloatField(default=0)
    avg_response_minutes = models.FloatField(default=60)

    def __str__(self):
        return f'{self.user.username} - {self.service_type}'
