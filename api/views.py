from django.shortcuts import redirect
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from beDoggo.models import User, Pet, Location, PetAccess
from .permissions import IsOwnerOrAdmin
from .serializers import UserSerializer, PetSerializer, LocationSerializer, PetAccessSerializer


def api_home(request):
    return redirect('/api/docs/')  # Redirige a la documentación Swagger


class GoogleLoginView(APIView):
    """
    Endpoint para manejar la autenticación con Google.
    """

    def post(self, request):
        # El cliente móvil enviará el token de Google
        token = request.data.get('token', None)

        if not token:
            return Response({"error": "El token es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verifica el token con los servidores de Google
            idinfo = id_token.verify_oauth2_token(token, requests.Request())

            """ Para produccion deberia ponerse esto
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), audience="YOUR_CLIENT_ID")
            """

            # Extraer información del usuario
            email = idinfo.get('email')
            first_name = idinfo.get('fullName', '')

            # Verifica si el usuario ya existe o crea uno nuevo
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "username": email.split('@')[0],
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
        return Pet.objects.filter(owner=self.request.user)  # Solo devuelve las mascotas del usuario autenticado

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
        return Location.objects.filter(pet__owner=self.request.user)


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Location.objects.all().order_by('id')
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


# Vistas para el modelo PetAccess
class PetAccessListCreateView(generics.ListCreateAPIView):
    serializer_class = PetAccessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PetAccess.objects.filter(user=self.request.user)

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
