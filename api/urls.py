from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PetListCreateView, PetDetailView, LocationListCreateView, LocationDetailView, \
    PetAccessListCreateView, PetAccessDetailView, GoogleLoginView, UserListView, AdminPetListView, \
    AdminPetAccessListView, api_home, LostPetsNearbyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Rutas para la documentación
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),

    path('admin/', include([
        path('pets/', AdminPetListView.as_view(), name='admin-pet-list'),
        path('pet-access/', AdminPetAccessListView.as_view(), name='admin-pet-access-list'),
    ])),

    path('', api_home, name='api-home'),  # Redirige a la documentación de Swagger
    path('users/', UserListView.as_view(), name='user-list'),
    path('pets/', PetListCreateView.as_view(), name='pet-list-create'),
    path('pets/<int:pk>/', PetDetailView.as_view(), name='pet-detail'),
    path('locations/', LocationListCreateView.as_view(), name='location-list-create'),
    path('locations/<int:pk>/', LocationDetailView.as_view(), name='location-detail'),
    path('pet-access/', PetAccessListCreateView.as_view(), name='pet-access-list-create'),
    path('pet-access/<int:pk>/', PetAccessDetailView.as_view(), name='pet-access-detail'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/google/', GoogleLoginView.as_view(), name='google-login'),

    path('lost-pets/', LostPetsNearbyView.as_view(), name='lost-pets-nearby'),
]
