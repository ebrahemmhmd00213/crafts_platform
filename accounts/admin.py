from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TechnicianProfile, ServiceType


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['id', 'username', 'email', 'role', 'phone', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('بيانات إضافية', {'fields': ('role', 'phone', 'latitude', 'longitude')}),
    )


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'service_type', 'status', 'avg_rating', 'avg_response_minutes']
    list_filter = ['status', 'service_type']
    search_fields = ['user__username', 'user__phone']
    actions = ['approve', 'reject']

    @admin.action(description='اعتماد الفنيين المحددين')
    def approve(self, request, queryset):
        queryset.update(status=TechnicianProfile.Status.APPROVED)

    @admin.action(description='رفض الفنيين المحددين')
    def reject(self, request, queryset):
        queryset.update(status=TechnicianProfile.Status.REJECTED)


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}