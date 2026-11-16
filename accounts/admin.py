from django.contrib import admin
from .models import User, TechnicianProfile


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'service_type', 'status']
    list_filter = ['status']
    actions = ['approve']

    @admin.action(description='Accreditation of designated technicians')
    def approve(self, request, queryset):
        queryset.update(status=TechnicianProfile.Status.APPROVED)

admin.site.register(User)