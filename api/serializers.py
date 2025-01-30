from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from beDoggo.models import User, Pet, AccessCode, Location, MedicalRecord, Veterinarian, GPSDevice


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uuid', 'email', 'first_name', 'last_name', 'phone', 'sex']


class GPSDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSDevice
        fields = '__all__'
        update_fields = ['is_active', 'activated_at']


class AssociateGPSDeviceSerializer(serializers.Serializer):
    gps_device_code = serializers.CharField(required=True)


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password']  # , 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            password=validated_data['password'],
            # first_name=validated_data.get('first_name', ''),
            # last_name=validated_data.get('last_name', ''),
        )
        return user


class VeterinarianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veterinarian
        fields = '__all__'


class PetSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    veterinarian = VeterinarianSerializer(read_only=True)
    gps_device = GPSDeviceSerializer(read_only=True)
    gps_device_code = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ['owner', 'veterinarian']

    def create(self, validated_data):
        gps_device_code = validated_data.pop('gps_device_code', None)
        gps_device = None

        if gps_device_code:
            try:
                gps_device = GPSDevice.objects.get(code=gps_device_code)
            except GPSDevice.DoesNotExist:
                raise serializers.ValidationError({"gps_device_code": "El dispositivo GPS no existe."})

        pet = Pet.objects.create(**validated_data, gps_device=gps_device)
        return pet

    def update(self, instance, validated_data):
        gps_device_code = validated_data.pop('gps_device_code', None)

        if gps_device_code:
            try:
                gps_device = GPSDevice.objects.get(code=gps_device_code)
                instance.gps_device = gps_device  # Asignar el nuevo dispositivo GPS
            except GPSDevice.DoesNotExist:
                raise serializers.ValidationError({"gps_device_code": "El dispositivo GPS no existe."})

        return super().update(instance, validated_data)


class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(source='location.y', required=True)  # Para `POST`
    longitude = serializers.FloatField(source='location.x', required=True)  # Para `POST`
    gps_device_code = serializers.CharField(required=True, write_only=True)  # Para `POST`
    # device = GPSDeviceSerializer(source='gps_device', read_only=True)  # Para `GET`
    pet = PetSerializer(source='gps_device.pet', read_only=True)  # 🔹 Devuelve toda la info de la mascota en `GET`

    class Meta:
        model = Location
        fields = ['uuid', 'timestamp', 'latitude', 'longitude', 'gps_device_code', 'pet']
        extra_kwargs = {
            'gps_device_code': {'write_only': True},  # 🔹 No aparecerá en `GET`, solo en `POST`
            'latitude': {'write_only': True},
            'longitude': {'write_only': True}
        }


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
    # email = serializers.EmailField(required=False)
    # name = serializers.CharField(required=False)


class LostPetSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    veterinarian = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Pet
        fields = ['name', 'sex', 'breed', 'color', 'age', 'weight', 'sterilized', 'observations', 'phone_emergency',
                  'owner', 'veterinarian', 'latitude', 'longitude']

    @extend_schema_field(UserSerializer)  # 🔹 Especifica que devuelve un usuario serializado
    def get_owner(self, obj):
        """ Devuelve la información del dueño como un diccionario. """
        if obj.owner:
            return {
                "uuid": obj.owner.uuid,
                "username": obj.owner.username,
                "email": obj.owner.email,
                "phone": obj.owner.phone,
            }
        return None

    @extend_schema_field(VeterinarianSerializer)  # 🔹 Devuelve un veterinario serializado
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

    @extend_schema_field(serializers.FloatField)  # 🔹 Devuelve un float (latitud)
    def get_latitude(self, obj):
        """ Devuelve la última latitud registrada del dispositivo GPS. """
        return obj.gps_device.locations.last().location.y if obj.gps_device and obj.gps_device.locations.exists() else None

    @extend_schema_field(serializers.FloatField)  # 🔹 Devuelve un float (longitud)
    def get_longitude(self, obj):
        """ Devuelve la última longitud registrada del dispositivo GPS. """
        return obj.gps_device.locations.last().location.x if obj.gps_device and obj.gps_device.locations.exists() else None
