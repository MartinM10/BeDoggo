from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from beDoggo.models import User, Pet, AccessCode, Location, MedicalRecord, Veterinarian, GPSDevice, SexUserChoices, \
    SexPetChoices


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uuid', 'email', 'username', 'first_name', 'last_name', 'birth_date', 'sex', 'phone',
                  'email_verified', 'address', 'prefix_phone', 'acquisition_channel', 'points', 'onboarding_completed',
                  'next_payment_date', 'accept_newsletter']


class GPSDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSDevice
        fields = '__all__'
        update_fields = ['is_active', 'activated_at']


class AssociateGPSDeviceSerializer(serializers.Serializer):
    gps_device_code = serializers.CharField(required=True)


class RegisterUserSerializer(serializers.ModelSerializer):
    sex = serializers.ChoiceField(choices=SexUserChoices.choices, required=False)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'email_verified', 'sex',
                  'profile_picture', 'address', 'prefix_phone', 'phone', 'birth_date', 'onboarding_completed']
        extra_kwargs = {'password': {'write_only': True}}  # Para que la contraseña no se muestre en la respuesta

    def create(self, validated_data):
        password = validated_data.pop('password', None)  # Extraer la contraseña antes de crear el usuario
        user = User(**validated_data)
        if password:
            user.set_password(password)  # Hashea la contraseña antes de guardarla
        user.save()
        return user


class VeterinarianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veterinarian
        fields = '__all__'


class PetSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    veterinarian = VeterinarianSerializer(read_only=True)
    gps_device = GPSDeviceSerializer(read_only=True)
    gps_device_code = serializers.CharField(required=False, write_only=True, allow_blank=True, allow_null=True)

    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ['owner', 'veterinarian']

    def validate(self, data):
        # Convertir todos los strings vacíos a None
        for field_name, value in dict(data).items():
            # Ignorar campos que no son string o son requeridos
            if isinstance(value, str) and value.strip() == "" and not self.fields[field_name].required:
                data[field_name] = None
        return data

    def create(self, validated_data):
        gps_device_code = validated_data.pop('gps_device_code', None)
        gps_device = None

        if gps_device_code and gps_device_code.strip():
            try:
                gps_device = GPSDevice.objects.get(code=gps_device_code)
            except GPSDevice.DoesNotExist:
                raise serializers.ValidationError({"gps_device_code": "El dispositivo GPS no existe."})

        request = self.context.get('request')
        if request and request.user:
            validated_data['owner'] = request.user
        
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


class OnboardingPetSerializer(serializers.ModelSerializer):
    gps_device_code = serializers.CharField(required=False, write_only=True)

    # Datos del usuario
    username = serializers.CharField(source='owner.username', required=False)
    first_name = serializers.CharField(source='owner.first_name', required=False)
    last_name = serializers.CharField(source='owner.last_name', required=False)
    accept_newsletter = serializers.BooleanField(source='owner.accept_newsletter', required=False)
    birth_date_user = serializers.DateField(source='owner.birth_date', required=False)
    sex_user = serializers.ChoiceField(source='owner.sex', choices=SexUserChoices.choices, required=False)

    # Datos de la mascota, con `_pet` para diferenciarlos
    sex_pet = serializers.ChoiceField(choices=SexPetChoices.choices, required=False)
    birth_date_pet = serializers.DateField(required=False)
    phone_emergency = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Pet
        fields = [
            'gps_device_code', 'name', 'sex_pet', 'breed', 'color', 'birth_date_pet', 'weight',
            'chip_number', 'chip_position', 'observations', 'sterilized', 'is_lost',
            'phone_emergency', 'image', 'shared_with',
            'username', 'sex_user', 'first_name', 'last_name', 'accept_newsletter', 'birth_date_user'
        ]


class PetSerializerWithShared(serializers.ModelSerializer):
    shared_with = serializers.SerializerMethodField()

    class Meta:
        model = Pet
        fields = '__all__'

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_shared_with(self, obj):
        return [{"uuid": user.uuid, "email": user.email} for user in obj.shared_with.all()]


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


class AccessCodeRequestSerializer(serializers.Serializer):
    code = serializers.CharField()


class AccessCodeSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = AccessCode
        fields = ['uuid', 'code', 'pet', 'pet_name', 'is_used', 'expires_at', 'created_at', 'created_by_email']
        read_only_fields = ['uuid', 'code', 'created_at', 'is_used', 'created_by_email']


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = '__all__'


class GoogleLoginSerializer(serializers.Serializer):
    # El token de ID recibido de Google (obligatorio para validar la identidad)
    id_token = serializers.CharField(max_length=5000, required=True, write_only=True)

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
        fields = ['name', 'sex', 'breed', 'color', 'birth_date', 'weight', 'sterilized', 'observations',
                  'phone_emergency', 'owner', 'veterinarian', 'latitude', 'longitude']

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
