from typing import Optional
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from beDoggo.models import User, Pet, AccessCode, Location, MedicalRecord, Veterinarian, GPSDevice


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uuid', 'email', 'first_name', 'last_name', 'phone', 'sex']


class GPSDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSDevice
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(source='location.y')
    longitude = serializers.FloatField(source='location.x')
    device = GPSDeviceSerializer(source='gps_device', read_only=True)
    pet = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['uuid', 'timestamp', 'latitude', 'longitude', 'device', 'pet']

    def get_pet(self, obj):
        """
        Retorna información de la mascota si el GPS tiene una asociada.
        """
        if isinstance(obj, dict):
            # Si `obj` es un diccionario, intenta obtener el GPS manualmente
            gps_device_id = obj.get('gps_device')
            if not gps_device_id:
                return None
            try:
                gps_device = GPSDevice.objects.get(id=gps_device_id)
                print(gps_device)
                if hasattr(gps_device, 'pet'):
                    return {
                        "name": gps_device.pet.name,
                        "age": gps_device.pet.age
                    }
            except GPSDevice.DoesNotExist:
                return None
        else:
            # Si `obj` es un modelo `Location`, accede a la relación correctamente
            if obj.gps_device and hasattr(obj.gps_device, 'pet'):
                return {
                    "name": obj.gps_device.pet.name,
                    "age": obj.gps_device.pet.age
                }
        return None


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


class VeterinarianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veterinarian
        fields = '__all__'


class PetSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    veterinarian = VeterinarianSerializer(read_only=True)
    gps_device = GPSDeviceSerializer()

    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ['owner', 'veterinarian']


class AccessCodeSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)

    class Meta:
        model = AccessCode
        fields = ['uuid', 'code', 'pet', 'pet_name', 'is_used', 'expires_at']


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = '__all__'


class GoogleLoginSerializer(serializers.Serializer):
    # El token de ID recibido de Google (obligatorio para validar la identidad)
    id_token = serializers.CharField(required=True, write_only=True)

    # Otros datos que se pueden enviar (aunque no son estrictamente necesarios para la autenticación)
    email = serializers.EmailField(required=False)
    name = serializers.CharField(required=False)


class LostPetSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    veterinarian = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Pet
        fields = ['name', 'sex', 'breed', 'color', 'age', 'weight', 'sterilized', 'observations', 'phone_emergency',
                  'owner', 'veterinarian', 'latitude', 'longitude']

    def get_owner(self, obj):
        """ Devuelve la información del dueño como un diccionario. """
        if obj.owner:
            return {
                "username": obj.owner.username,
                "email": obj.owner.email,
                "phone": obj.owner.phone,
            }
        return None

    def get_veterinarian(self, obj):
        """ Devuelve la información del veterinario que tiene asociado como un diccionario. """
        if obj.veterinarian:
            return {
                "clinic_name": obj.veterinarian.clinic_name,
                "clinic_address": obj.veterinarian.clinic_address,
                "clinic_phone": obj.veterinarian.clinic_phone,
                "available_hours": obj.veterinarian.available_hours,
            }
        return None

    def get_latitude(self, obj):
        """ Devuelve la última latitud registrada del dispositivo GPS. """
        return obj.gps_device.locations.last().location.y if obj.gps_device and obj.gps_device.locations.exists() else None

    def get_longitude(self, obj):
        """ Devuelve la última longitud registrada del dispositivo GPS. """
        return obj.gps_device.locations.last().location.x if obj.gps_device and obj.gps_device.locations.exists() else None
