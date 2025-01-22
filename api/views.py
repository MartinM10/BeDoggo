from django.shortcuts import redirect
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from beDoggo.models import User, Pet, Location, PetAccess
from .permissions import IsOwnerOrAdmin
from .serializers import UserSerializer, PetSerializer, LocationSerializer, PetAccessSerializer, LostPetSerializer, \
    GoogleLoginSerializer
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D  # Distancia
from django.contrib.gis.db.models.functions import Distance
from drf_spectacular.utils import extend_schema, OpenApiParameter


def api_home(request):
    return redirect('/api/docs/')  # Redirige a la documentación Swagger


class GoogleLoginView(APIView):
    """
    Endpoint para manejar la autenticación con Google.
    """
    serializer_class = GoogleLoginSerializer

    def post(self, request):
        # El cliente móvil enviará el token de Google
        token = request.data.get('token', None)

        if not token:
            return Response({"error": "El token es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verifica el token con los servidores de Google
            # para produccion descomentar la siguiente linea
            # idinfo = id_token.verify_oauth2_token(token, requests.Request(), audience=settings.GOOGLE_CLIENT_ID)
            idinfo = id_token.verify_oauth2_token(token, requests.Request())

            # Extraer información del usuario
            email = idinfo.get('email')
            first_name = idinfo.get('given_name', '')  # Usar 'given_name' para el primer nombre
            last_name = idinfo.get('family_name', '')  # Usar 'family_name' para el apellido

            # Verifica si el usuario ya existe o crea uno nuevo
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": email.split('@')[0],  # El nombre de usuario se genera del email
                },
            )

            # Genera un token JWT para el usuario
            refresh = RefreshToken.for_user(user)

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            })

        except ValueError as e:
            # El token no es válido o ha expirado
            return Response({"error": "Token inválido o expirado.", "details": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


# Vistas para el modelo Pet
class PetListCreateView(generics.ListCreateAPIView):
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user).order_by('id')
        # Solo devuelve las mascotas del usuario autenticado

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return Pet.objects.all().order_by('id')


# Vista para que un administrador obtenga todas las mascotas
class AdminPetListView(generics.ListAPIView):
    queryset = Pet.objects.all().order_by('id')
    serializer_class = PetSerializer
    permission_classes = [IsAdminUser]  # Solo accesible para administradores


# Vistas para el modelo Location
class LocationListCreateView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Solo devuelve ubicaciones de las mascotas del usuario
        return Location.objects.filter(pet__owner=self.request.user).order_by('id')


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Location.objects.all().order_by('id')
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


# Vistas para el modelo PetAccess
class PetAccessListCreateView(generics.ListCreateAPIView):
    serializer_class = PetAccessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PetAccess.objects.filter(user=self.request.user).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PetAccessDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PetAccess.objects.all().order_by('id')
    serializer_class = PetAccessSerializer
    permission_classes = [IsAuthenticated]


# Vista para que un administrador obtenga todos los accesos a mascotas
class AdminPetAccessListView(generics.ListAPIView):
    queryset = PetAccess.objects.all().order_by('id')
    serializer_class = PetAccessSerializer
    permission_classes = [IsAdminUser]


class UserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


@extend_schema(
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
class LostPetsNearbyView(APIView):
    permission_classes = [AllowAny]  # No Requiere autenticación

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
