from typing import Optional
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from beDoggo.models import User, Pet, Location, PetAccess


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'address', 'on_boarding']


class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = ['id', 'name', 'breed', 'age', 'observations', 'is_lost', 'owner']
        read_only_fields = ['owner']


class LocationSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Location
        geo_field = 'location'  # Este es el campo geoespacial en el modelo
        fields = ['id', 'location', 'timestamp', 'pet']


class PetAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetAccess
        fields = ['id', 'user', 'pet']


class GoogleLoginSerializer(serializers.Serializer):
    # El token de acceso que recibimos de Google
    access_token = serializers.CharField(required=True, write_only=True)

    # Si también quieres el token de ID para verificar los datos del usuario, puedes incluirlo
    id_token = serializers.CharField(required=False, write_only=True)

    # Otras posibles validaciones o datos que quieras procesar
    # Por ejemplo, puedes recibir el correo electrónico o el nombre del usuario
    email = serializers.EmailField(required=False)
    name = serializers.CharField(required=False)


class LostPetSerializer(serializers.ModelSerializer):
    owner_username = serializers.SerializerMethodField()
    owner_phone = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Pet
        fields = ['name', 'breed', 'age', 'owner_username', 'owner_phone', 'owner_email', 'latitude',
                  'longitude']  # Aquí se agrega `owner_username`

    def get_owner_username(self, obj) -> Optional[str]:
        # Aseguramos que `obj` es la instancia de la mascota (Pet)
        return obj.owner.username if obj.owner and obj.owner.username else None  # Usamos `obj` y no `self.instance`

    def get_owner_phone(self, obj) -> Optional[str]:
        return obj.owner.phone if obj.owner and obj.owner.phone else None

    def get_owner_email(self, obj) -> Optional[str]:
        return obj.owner.email if obj.owner and obj.owner.email else None

    @extend_schema_field(str)
    def get_latitude(self, obj) -> Optional[float]:
        # Obtener la última ubicación de la mascota (si existe)
        location = obj.locations.last()
        return location.location.y if location else None

    @extend_schema_field(str)
    def get_longitude(self, obj) -> Optional[float]:
        # Obtener la última ubicación de la mascota (si existe)
        location = obj.locations.last()
        return location.location.x if location else None
