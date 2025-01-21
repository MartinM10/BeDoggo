from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.contrib.gis.db import models


class User(AbstractUser):
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    on_boarding = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.username}"


class Pet(models.Model):
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100, blank=True, null=True)
    age = models.PositiveIntegerField()
    observations = models.TextField(blank=True, null=True)
    is_lost = models.BooleanField(default=False)
    owner = models.ForeignKey(User, related_name='pets', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({'Lost' if self.is_lost else 'Not Lost'})"


class Location(models.Model):
    location = models.PointField()  # Usamos PointField para las coordenadas geográficas
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    pet = models.ForeignKey(Pet, related_name='locations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location of {self.pet.name} at {self.timestamp}"


class PetAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accessible_pets")
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="access_grants")

    class Meta:
        unique_together = ("user", "pet")
        verbose_name = "Pet Access"
        verbose_name_plural = "Pet Accesses"

    def __str__(self):
        return f"{self.user.email} has access to {self.pet.name}"
