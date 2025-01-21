from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from beDoggo.models import User, Pet, Location, PetAccess
from .serializers import UserSerializer, PetSerializer, LocationSerializer, PetAccessSerializer


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
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PetDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated]


# Vistas para el modelo Location
class LocationListCreateView(generics.ListCreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


# Vistas para el modelo PetAccess
class PetAccessListCreateView(generics.ListCreateAPIView):
    queryset = PetAccess.objects.all()
    serializer_class = PetAccessSerializer
    permission_classes = [IsAuthenticated]


class PetAccessDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PetAccess.objects.all()
    serializer_class = PetAccessSerializer
    permission_classes = [IsAuthenticated]
