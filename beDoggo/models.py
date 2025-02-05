import hashlib
import random
import string
import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class SexUserChoices(models.TextChoices):
    MALE = 'Male', _('Hombre')
    FEMALE = 'Female', _('Mujer')
    OTHER = 'Other', _('Otros')
    PREFER_NOT_TO_ANSWER = 'PreferNotAnswer', _('Prefiero no responder')


class SexPetChoices(models.TextChoices):
    MALE = 'Male', _('Macho')
    FEMALE = 'Female', _('Hembra')


# Modelo de usuario personalizado
class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.URLField(null=True, blank=True)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    address = models.TextField(blank=True, null=True)
    prefix_phone = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    sex = models.CharField(max_length=20, choices=SexUserChoices.choices, blank=True, null=True)

    class AcquisitionChannelChoices(models.TextChoices):
        ADVERTISEMENT = 'Advertisement', _('Publicidad')
        RECOMMENDATION = 'Recommendation', _('Recomendación')
        SOCIAL_MEDIA = 'Social Media', _('Redes Sociales')

    acquisition_channel = models.CharField(
        max_length=20,
        choices=AcquisitionChannelChoices.choices,
        blank=True,
        null=True
    )
    birth_date = models.DateField(blank=True, null=True)
    points = models.PositiveIntegerField(default=0)
    onboarding_completed = models.BooleanField(default=False)
    next_payment_date = models.DateTimeField(blank=True, null=True)
    accept_newsletter = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # REQUIRED_FIELDS = ['first_name', 'last_name']
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0]  # 🔹 Genera username basado en el email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username if self.username else self.first_name} ({self.email})"


# Modelo de veterinarios
class Veterinarian(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='veterinarian_profile')
    vet_license_number = models.CharField(max_length=50, unique=True)
    clinic_name = models.CharField(max_length=100, blank=True, null=True)
    clinic_address = models.TextField(blank=True, null=True)
    clinic_phone = models.CharField(max_length=20, blank=True, null=True)
    available_hours = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Veterinarian: {self.user.get_full_name()} - {self.clinic_name or 'No clinic'}"


def generate_device_code():
    """Genera un código único de 6 caracteres alfanuméricos."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class GPSDevice(models.Model):
    code = models.CharField(max_length=10, unique=True, blank=False, null=False)  # 🔹 Ahora es obligatorio
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Genera un código único si no se proporciona manualmente."""
        if not self.code:
            self.code = generate_device_code()
            while GPSDevice.objects.filter(code=self.code).exists():
                self.code = generate_device_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Device {self.code} (Active: {self.is_active})"


# Modelo de mascotas
class Pet(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    sex = models.CharField(max_length=10, choices=SexPetChoices.choices, blank=True, null=True)
    breed = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    weight = models.FloatField(null=True, blank=True)
    chip_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    chip_position = models.CharField(max_length=100, null=True, blank=True)
    observations = models.TextField(blank=True, null=True)
    sterilized = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)
    phone_emergency = models.CharField(max_length=20, blank=True, null=True)
    passport = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # Relaciones
    owner = models.ForeignKey(User, related_name='owned_pets', on_delete=models.CASCADE)
    gps_device = models.OneToOneField(GPSDevice, on_delete=models.SET_NULL, blank=True, null=True)
    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.SET_NULL, blank=True, null=True,
                                     related_name='pets')
    shared_with = models.ManyToManyField(User, related_name='shared_pets', blank=True)

    image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({'Lost' if self.is_lost else 'Not Lost'})"


# Modelo de historial médico
class MedicalRecord(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    pet = models.ForeignKey(Pet, related_name="medical_records", on_delete=models.CASCADE)
    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.CASCADE, related_name="medical_records")
    date = models.DateTimeField(auto_now_add=now)
    visit_reason = models.CharField(max_length=200)
    diagnosis = models.TextField(blank=True, null=True)
    treatment = models.TextField(blank=True, null=True)
    medication = models.TextField(blank=True, null=True)
    vaccines = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    test_results = models.TextField(blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    next_visit = models.DateField(blank=True, null=True)
    attachments = models.URLField(blank=True, null=True)
    images = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Medical Record for {self.pet.name} on {self.date}"


# Modelo de localización
class Location(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    location = models.PointField()  # Coordenadas
    timestamp = models.DateTimeField(auto_now_add=True)

    gps_device = models.ForeignKey(GPSDevice, on_delete=models.CASCADE, related_name='locations', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location from device {self.gps_device.uuid} at {self.timestamp}"


# Modelo de códigos de acceso
class AccessCode(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    code = models.CharField(max_length=64, unique=True)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='access_codes')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_codes')
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            unique_data = f"{self.pet.uuid}{self.created_by.uuid}{uuid.uuid4()}"
            self.code = hashlib.sha256(unique_data.encode()).hexdigest()
        # Establecer expiración por defecto a 1 semana
        if not self.expires_at:
            self.expires_at = now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @staticmethod
    def validate_code(code, user):
        try:
            access_code = AccessCode.objects.get(code=code)
        except AccessCode.DoesNotExist:
            raise ValidationError("The code does not exist.")
        if access_code.is_used:
            raise ValidationError("Code already used.")
        if access_code.expires_at and access_code.expires_at < now():
            raise ValidationError("The code has expired.")
        access_code.pet.shared_with.add(user)  # Otorga acceso al usuario
        access_code.is_used = True
        access_code.save()
        return access_code.pet

    def __str__(self):
        return f"Code for {self.pet.name} (Used: {self.is_used})"
