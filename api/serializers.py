from typing import Optional
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from beDoggo.models import User, Pet, AccessCode, Location, MedicalRecord, Veterinarian


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'uuid', 'email', 'first_name', 'last_name', 'phone', 'sex']


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


class PetSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ['owner']


class AccessCodeSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)

    class Meta:
        model = AccessCode
        fields = ['id', 'code', 'pet', 'pet_name', 'is_used', 'expires_at']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class VeterinarianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veterinarian
        fields = '__all__'


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = '__all__'


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
                  'longitude']

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
