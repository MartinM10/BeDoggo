from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import (
    api_home, GoogleLoginView, RegisterUserView,
    PetListCreateView, PetDetailView, PetAccessCodeView, AccessCodeValidationView,
    LostPetsNearbyView, LocationListCreateView, VeterinarianListCreateView, VeterinarianDetailView,
    MedicalRecordListCreateView, MedicalRecordDetailView, PetSearchView, SharedPetsView, OnboardingView,
    GPSDeviceListCreateView, GPSDeviceDetailView, AssociateGPSDeviceView, UserProfileView
)

urlpatterns = [
    # Documentación
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),

    # Home
    path('', api_home, name='api-home'),

    # Usuarios y autenticación
    path('auth/google/', GoogleLoginView.as_view(), name='google-login'),
    path('auth/register/', RegisterUserView.as_view(), name='register'),
    path("me/", UserProfileView.as_view(), name="user-profile"),
    path('onboarding/', OnboardingView.as_view(), name='onboarding'),

    # Mascotas
    path('pets/', PetListCreateView.as_view(), name='pet-list-create'),
    path('pets/<uuid:uuid>/', PetDetailView.as_view(), name='pet-detail'),
    path('pets/<uuid:pet_id>/access-code/', PetAccessCodeView.as_view(), name='pet-access-code'),
    path('pets/access-code/validate/', AccessCodeValidationView.as_view(), name='access-code-validate'),
    path('pets/search/', PetSearchView.as_view(), name='pet-search'),
    path('pets/shared/', SharedPetsView.as_view(), name='shared-pets'),
    path('pets/<uuid:pet_id>/associate-device/', AssociateGPSDeviceView.as_view(), name='associate-device'),

    # Dispositivos GPS
    path('gps-devices/', GPSDeviceListCreateView.as_view(), name='gps-device-list-create'),
    path('gps-devices/<str:code>/', GPSDeviceDetailView.as_view(), name='gps-device-detail'),

    # Ubicaciones
    path('locations/', LocationListCreateView.as_view(), name='location-list-create'),
    # path('locations/<uuid:uuid>/', LocationDetailView.as_view(), name='location-detail'),
    path('locations/lost-pets/', LostPetsNearbyView.as_view(), name='lost-pets'),

    # Veterinarios
    path('veterinarians/', VeterinarianListCreateView.as_view(), name='veterinarian-list-create'),
    path('veterinarians/<int:pk>/', VeterinarianDetailView.as_view(), name='veterinarian-detail'),

    # Historial Médico
    path('medical-records/<uuid:pet_id>/', MedicalRecordListCreateView.as_view(), name='medical-record-list-create'),
    path('medical-records/<uuid:record_id>/', MedicalRecordDetailView.as_view(), name='medical-record-detail'),

    # JWT Tokens
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
