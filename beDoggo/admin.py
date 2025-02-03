from django.contrib import admin
from .models import User, Veterinarian, GPSDevice, Pet, MedicalRecord
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _


# Administrador de Usuario
class UserAdmin(BaseUserAdmin):  # Hereda de BaseUserAdmin
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': (
            'username',
            'first_name',
            'last_name',
            'profile_picture',
            'address',
            'prefix_phone',
            'phone',
            'sex',
            'acquisition_channel',
            'birth_date',
            'points',
            'onboarding_completed',
            'next_payment_date'
        )}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'groups',
                'user_permissions'),
        }),
    )
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)


admin.site.register(User, UserAdmin)


# Administrador de Veterinarios
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = ('user', 'vet_license_number', 'clinic_name', 'created_at', 'updated_at')
    search_fields = ('user__email', 'vet_license_number', 'clinic_name')
    ordering = ('created_at',)


admin.site.register(Veterinarian, VeterinarianAdmin)


# Administrador de Dispositivos GPS
class GPSDeviceAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_active', 'activated_at', 'created_at', 'updated_at')
    search_fields = ('code',)
    ordering = ('created_at',)


admin.site.register(GPSDevice, GPSDeviceAdmin)


# Administrador de Mascotas
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'sex', 'birth_date', 'weight', 'is_lost', 'gps_device')
    search_fields = ('name', 'owner__email', 'chip_number')
    list_filter = ('sex', 'is_lost')
    ordering = ('name',)


admin.site.register(Pet, PetAdmin)


# Administrador de Registros Médicos
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('pet', 'veterinarian', 'date', 'visit_reason', 'diagnosis')
    search_fields = ('pet__name', 'veterinarian__user__email', 'visit_reason', 'diagnosis')
    list_filter = ('date',)
    ordering = ('date',)


admin.site.register(MedicalRecord, MedicalRecordAdmin)
