from django.shortcuts import redirect
from django.utils.timezone import now
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken

from BeDoggo import settings
from beDoggo.models import User, Pet, AccessCode, Location, MedicalRecord, Veterinarian, GPSDevice
from .serializers import UserSerializer, PetSerializer, LostPetSerializer, \
    GoogleLoginSerializer, RegisterUserSerializer, AccessCodeSerializer, LocationSerializer, MedicalRecordSerializer, \
    VeterinarianSerializer, GPSDeviceSerializer
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D  # Distancia
from django.contrib.gis.db.models.functions import Distance
from drf_spectacular.utils import extend_schema, OpenApiParameter


def api_home(request):
    return redirect('/api/docs/')  # Redirige a la documentación Swagger


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Inicio de sesión con Google",
        description="Autentica al usuario con su token de Google y devuelve tokens JWT.",
        request=GoogleLoginSerializer,
        responses={
            200: UserSerializer,
            400: {"error": "Token inválido o expirado."},
        },
    )
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data.get('id_token')  # Ahora obtenemos el id_token
            try:
                # Crear una solicitud de tipo 'requests' para pasarla al método de verificación de Google
                google_request = GoogleRequest()

                # Verificar el token con Google
                # idinfo = id_token.verify_oauth2_token(token, google_request, settings.GOOGLE_CLIENT_ID)
                idinfo = id_token.verify_oauth2_token(token, google_request)
                # Obtener la información relevante del usuario
                email = idinfo.get('email')
                email_verified = idinfo.get('email_verified', False)
                first_name = idinfo.get('given_name', '')
                last_name = idinfo.get('family_name', '')
                picture = idinfo.get('picture', '')  # Foto de perfil (opcional)

                # Obtener o crear un nuevo usuario
                user, created = User.objects.get_or_create(
                    email=email,
                    email_verified=email_verified,
                    defaults={
                        "username": email.split('@')[0],  # Utilizamos el email como username por defecto
                        "first_name": first_name,
                        "last_name": last_name,
                        "profile_picture": picture,
                    },
                )
                # Generar tokens de acceso (JWT)
                refresh = RefreshToken.for_user(user)
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                })
            except ValueError:
                return Response({"error": "Token inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Registrar usuario",
        description="Registra un nuevo usuario en el sistema y devuelve tokens JWT.",
        request=RegisterUserSerializer,
        responses={
            201: {
                "message": "Usuario registrado exitosamente",
                "access": "token_access",
                "refresh": "token_refresh"
            },
            400: {"error": "Errores de validación."},
        },
    )
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                "message": "Usuario registrado exitosamente",
                "access": access_token,
                "refresh": str(refresh),
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Completar onboarding y registrar mascota",
        description="Permite a los usuarios completar el proceso de onboarding y registrar una mascota. "
                    "Si se proporciona un `gps_device`, se asociará con la mascota.",
        request=PetSerializer,
        responses={201: PetSerializer, 400: {"error": "Errores de validación."}}
    )
    def post(self, request):
        user = request.user  # Usuario autenticado

        # Procesar datos de la mascota
        pet_data = request.data.copy()

        # Si el usuario proporciona un GPSDevice, se asocia
        gps_device_code = pet_data.get("gps_device_code")
        if gps_device_code:
            try:
                gps_device, created = GPSDevice.objects.get_or_create(code=gps_device_code)
                pet_data['gps_device_code'] = gps_device.id  # Asignar el GPS a la mascota
            except GPSDevice.DoesNotExist:
                return Response({"error": "El dispositivo GPS proporcionado no existe."},
                                status=status.HTTP_400_BAD_REQUEST)

        # Serializar y guardar la mascota con el dueño asignado manualmente
        serializer = PetSerializer(data=pet_data)
        if serializer.is_valid():
            pet = serializer.save(owner=user)  # 🔹 Aquí se asigna el dueño correctamente
            return Response(PetSerializer(pet).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PetListCreateView(generics.ListCreateAPIView):
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar y registrar mascotas",
        description="Obtén todas tus mascotas registradas o registra una nueva.",
        responses={200: PetSerializer(many=True)},
    )
    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'  # Se usará 'uuid' en lugar del ID por defecto

    @extend_schema(summary="Detalles de una mascota")
    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user)


class PetAccessCodeView(generics.CreateAPIView):
    serializer_class = AccessCodeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Generar código de acceso para compartir una mascota",
        responses={201: AccessCodeSerializer},
    )
    def post(self, request, pet_id):
        pet = Pet.objects.get(uuid=pet_id, owner=request.user)
        access_code = AccessCode.objects.create(pet=pet, created_by=request.user)
        serializer = AccessCodeSerializer(access_code)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AssociateGPSDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Asociar dispositivo GPS a una mascota",
        description="Permite a los usuarios asociar un dispositivo GPS a una mascota.",
        request=PetSerializer,
        responses={200: PetSerializer}
    )
    def post(self, request, pet_id):
        pet = Pet.objects.get(uuid=pet_id, owner=request.user)
        device_id = request.data.get('device_id')
        device = GPSDevice.objects.get(uuid=device_id)
        pet.device = device
        pet.save()
        serializer = PetSerializer(pet)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PetSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Buscar mascotas por email o chip",
        description="Permite a los veterinarios buscar mascotas por el email del dueño o por el código del chip.",
        parameters=[
            OpenApiParameter(
                name="email",
                description="Email del dueño",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="chip_number",
                description="Código del chip de la mascota",
                required=False,
                type=str
            ),
        ],
        responses={200: PetSerializer(many=True)}
    )
    def get(self, request):
        email = request.query_params.get('email')
        chip_number = request.query_params.get('chip_number')
        if email:
            pets = Pet.objects.filter(owner__email=email)
        elif chip_number:
            pets = Pet.objects.filter(chip_number=chip_number)
        else:
            return Response({"error": "Debe proporcionar un email o un número de chip."},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = PetSerializer(pets, many=True)
        return Response(serializer.data)


class SharedPetsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar mascotas compartidas",
        description="Permite a los usuarios ver las mascotas a las que tienen acceso a través de un código de acceso.",
        responses={200: PetSerializer(many=True)}
    )
    def get(self, request):
        shared_pets = Pet.objects.filter(shared_with=request.user)
        serializer = PetSerializer(shared_pets, many=True)
        return Response(serializer.data)


class AccessCodeValidationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Validar un código de acceso",
        request=AccessCodeSerializer,
        responses={200: {"message": "Acceso concedido"}},
    )
    def post(self, request):
        code = request.data.get('code')
        try:
            access_code = AccessCode.validate_code(code)
            pet = access_code.pet
            pet.shared_with.add(request.user)
            return Response({"message": f"Acceso concedido a la mascota {pet.name}"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LocationListCreateView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar y crear ubicaciones",
        description="Permite a los usuarios listar las ubicaciones de sus mascotas asociadas a dispositivos GPS o crear una nueva ubicación para una mascota específica.",
        request=LocationSerializer,
        responses={
            200: LocationSerializer,
            400: {"error": "Se requieren latitude y longitude"},
            403: {"error": "No tienes permiso para usar este dispositivo."},
            404: {"error": "El dispositivo GPS no existe."},
        },
    )
    def get_queryset(self):
        return Location.objects.filter(
            gps_device__pet__owner=self.request.user
        ).order_by('-timestamp')

    def perform_create(self, serializer):
        latitude = self.request.data.get('latitude')
        longitude = self.request.data.get('longitude')
        gps_code = self.request.data.get('gps_device')

        # Verifica que latitude y longitude estén presentes
        if not latitude or not longitude:
            return Response({"error": "Se requieren latitude y longitude"}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica si el GPS existe antes de continuar
        gps_device = None
        try:
            gps_device = GPSDevice.objects.get(code=gps_code)
        except GPSDevice.DoesNotExist:
            return Response({"error": "El dispositivo GPS no existe."}, status=status.HTTP_404_NOT_FOUND)

        # 🔹 Verifica que el GPS tenga una mascota asociada y que el usuario sea el dueño
        if not hasattr(gps_device, 'pet') or gps_device.pet.owner != self.request.user:
            return Response({"error": "No tienes permiso para usar este dispositivo."},
                            status=status.HTTP_403_FORBIDDEN)

        # 🔹 Verifica que el GPS esté activado
        if not gps_device.is_active:
            return Response({"error": "El dispositivo GPS no está activado."}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Crea el objeto Location si todas las validaciones pasan
        point = Point(float(longitude), float(latitude))
        serializer.save(location=point, gps_device=gps_device)


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Location.objects.filter(gps_device__pet__owner=self.request.user)


class LostPetsNearbyView(APIView):
    permission_classes = [AllowAny]  # No Requiere autenticación
    """
        Endpoint para buscar mascotas perdidas dentro de la distancia especificada.
    """

    @extend_schema(
        summary="buscar mascotas perdidas dentro de la distancia especificada",
        description="proporcionando latitud, longitud y distancia busca mascotas perdidas dentro en la zona "
                    "dentro de la distancia especificada.",
        parameters=[
            OpenApiParameter(
                name="latitude",
                description="Latitud del usuario",
                required=True,
                type=float,
                default=36.71040344238281
            ),
            OpenApiParameter(
                name="longitude",
                description="Longitud del usuario",
                required=True,
                type=float,
                default=-4.440666198730469
            ),
            OpenApiParameter(
                name="distance",
                description="Distancia en kilómetros para buscar mascotas (por defecto: 2 km)",
                required=False,
                type=float,
                default=2
            ),
        ],
        responses={200: LostPetSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        latitude = float(request.query_params.get('latitude'))
        longitude = float(request.query_params.get('longitude'))
        distance = float(request.query_params.get('distance'))

        # Crear el punto de ubicación del usuario
        user_location = Point(longitude, latitude, srid=4326)

        # Filtrar mascotas perdidas dentro de la distancia especificada
        lost_pets = Pet.objects.filter(
            is_lost=True,
            # gps_device__locations__location__distance_lte=(user_location, D(km=distance))  # <-- CAMBIO AQUÍ
            gps_device__isnull=False,  # Solo mascotas con GPS
            gps_device__locations__location__distance_lte=(user_location, D(km=distance))
        ).annotate(
            distance=Distance('gps_device__locations__location', user_location)  # <-- Y AQUÍ
        ).select_related('owner', 'gps_device').prefetch_related('gps_device__locations').order_by('distance')
        # Serializar los resultados
        serializer = LostPetSerializer(lost_pets, many=True)
        return Response(serializer.data)


class VeterinarianListCreateView(generics.ListCreateAPIView):
    queryset = Veterinarian.objects.all()
    serializer_class = VeterinarianSerializer
    permission_classes = [IsAdminUser]  # Solo el admin puede ver y registrar veterinarios

    @extend_schema(
        summary="Listar y registrar veterinarios",
        description="Lista todos los veterinarios registrados. Solo accesible por administradores.",
        responses={200: VeterinarianSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Registrar un veterinario",
        description="Crea un nuevo veterinario. Solo accesible por administradores.",
        request=VeterinarianSerializer,
        responses={201: VeterinarianSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class VeterinarianDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Veterinarian.objects.all()
    serializer_class = VeterinarianSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Obtener detalles de un veterinario",
        description="Devuelve la información de un veterinario específico.",
        responses={200: VeterinarianSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar un veterinario",
        description="Modifica los datos de un veterinario. Solo accesible por administradores.",
        request=VeterinarianSerializer,
        responses={200: VeterinarianSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Eliminar un veterinario",
        description="Elimina un veterinario del sistema. Solo accesible por administradores.",
        responses={204: None}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class MedicalRecordListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar historial médico de una mascota",
        description="Obtiene todos los registros médicos de una mascota.",
        responses={200: MedicalRecordSerializer(many=True)}
    )
    def get(self, request, pet_id):
        pet = Pet.objects.get(uuid=pet_id)
        if pet.owner != request.user and not pet.shared_with.filter(id=request.user.id).exists():
            return Response({"error": "No tienes permiso para ver este historial."}, status=status.HTTP_403_FORBIDDEN)
        medical_records = MedicalRecord.objects.filter(pet=pet)
        serializer = MedicalRecordSerializer(medical_records, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Crear un registro médico",
        description="Permite a un veterinario añadir información médica a una mascota.",
        request=MedicalRecordSerializer,
        responses={201: MedicalRecordSerializer}
    )
    def post(self, request, pet_id):
        pet = Pet.objects.get(uuid=pet_id)
        if not hasattr(request.user, 'veterinarian_profile'):
            return Response({"error": "Solo los veterinarios pueden añadir registros médicos."},
                            status=status.HTTP_403_FORBIDDEN)
        data = request.data.copy()
        data['pet'] = pet.id
        data['veterinarian'] = request.user.veterinarian_profile.id
        serializer = MedicalRecordSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MedicalRecordDetailView(generics.RetrieveAPIView):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtener un registro médico",
        description="Devuelve los detalles de un registro médico específico.",
        responses={200: MedicalRecordSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class GPSDeviceListCreateView(generics.ListCreateAPIView):
    queryset = GPSDevice.objects.all()
    serializer_class = GPSDeviceSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar y registrar dispositivos GPS",
        description="Devuelve todos los dispositivos GPS registrados. "
                    "También permite a un administrador registrar un nuevo dispositivo.",
        responses={200: GPSDeviceSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Registrar un nuevo dispositivo GPS",
        description="Registra un nuevo dispositivo GPS en el sistema.",
        request=GPSDeviceSerializer,
        responses={201: GPSDeviceSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class GPSDeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GPSDevice.objects.all()
    serializer_class = GPSDeviceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "code"

    @extend_schema(
        summary="Obtener detalles de un dispositivo GPS",
        description="Devuelve la información de un dispositivo GPS específico.",
        responses={200: GPSDeviceSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar un dispositivo GPS",
        description="Modifica los datos de un dispositivo GPS.",
        request=GPSDeviceSerializer,
        responses={200: GPSDeviceSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Eliminar un dispositivo GPS",
        description="Elimina un dispositivo GPS del sistema.",
        responses={204: None}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class ActivateGPSDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Activar un dispositivo GPS",
        description="Activa un dispositivo GPS por su código.",
        responses={200: {"message": "Dispositivo activado exitosamente."}}
    )
    def post(self, request, code):
        try:
            gps_device = GPSDevice.objects.get(code=code)
            if gps_device.is_active:
                return Response({"error": "El dispositivo ya está activado."}, status=status.HTTP_400_BAD_REQUEST)

            gps_device.is_active = True
            gps_device.activated_at = now()
            gps_device.save()
            return Response({"message": "Dispositivo activado exitosamente."}, status=status.HTTP_200_OK)
        except GPSDevice.DoesNotExist:
            return Response({"error": "El dispositivo GPS no existe."}, status=status.HTTP_404_NOT_FOUND)


class DeactivateGPSDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Desactivar un dispositivo GPS",
        description="Desactiva un dispositivo GPS por su código.",
        responses={200: {"message": "Dispositivo desactivado exitosamente."}}
    )
    def post(self, request, code):
        try:
            gps_device = GPSDevice.objects.get(code=code)
            if not gps_device.is_active:
                return Response({"error": "El dispositivo ya está desactivado."}, status=status.HTTP_400_BAD_REQUEST)

            gps_device.is_active = False
            gps_device.save()
            return Response({"message": "Dispositivo desactivado exitosamente."}, status=status.HTTP_200_OK)
        except GPSDevice.DoesNotExist:
            return Response({"error": "El dispositivo GPS no existe."}, status=status.HTTP_404_NOT_FOUND)
