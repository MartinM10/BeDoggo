from django.shortcuts import redirect
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from beDoggo.models import User, Pet, AccessCode, Location, MedicalRecord, Veterinarian, GPSDevice
from .serializers import UserSerializer, PetSerializer, LostPetSerializer, \
    GoogleLoginSerializer, RegisterUserSerializer, AccessCodeSerializer, LocationSerializer, MedicalRecordSerializer, \
    VeterinarianSerializer
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
            token = serializer.validated_data.get('access_token')
            try:
                idinfo = id_token.verify_oauth2_token(token, requests.Request())
                email = idinfo.get('email')
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "username": email.split('@')[0],
                        "first_name": idinfo.get('given_name', ''),
                        "last_name": idinfo.get('family_name', ''),
                    },
                )
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
        description="Registra un nuevo usuario en el sistema.",
        request=RegisterUserSerializer,
        responses={
            201: {"message": "Usuario registrado exitosamente"},
            400: {"error": "Errores de validación."},
        },
    )
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Usuario registrado exitosamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Completar onboarding",
        description="Permite a los usuarios completar el proceso de onboarding.",
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def post(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(onboarding_completed=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
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

    @extend_schema(summary="Detalles de una mascota")
    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user)


class PetAccessCodeView(APIView):
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

    def get_queryset(self):
        # Solo devuelve ubicaciones de las mascotas del usuario
        return Location.objects.filter(pet__owner=self.request.user).order_by('id')


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Solo permite ver ubicaciones de mascotas del usuario
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
            locations__location__distance_lte=(user_location, D(km=distance))
        ).annotate(
            distance=Distance('locations__location', user_location)
        ).select_related('owner').order_by('distance')  # Ordenar por distancia

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
