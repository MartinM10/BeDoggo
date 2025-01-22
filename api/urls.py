from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PetListCreateView, PetDetailView, LocationListCreateView, LocationDetailView, \
    PetAccessListCreateView, PetAccessDetailView, GoogleLoginView, UserListView, AdminPetListView, \
    AdminPetAccessListView, api_home
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

# Configuración de drf-yasg con esquema de seguridad JWT
schema_view = get_schema_view(
    openapi.Info(
        title="BeDoggo API",
        default_version='v1',
        description="API para la gestión de mascotas, ubicaciones y accesos.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="soporte@bedoggo.com"),
        license=openapi.License(name="MIT License"),
    ),
    # url="http://localhost:8080/",
    public=True,
    permission_classes=(AllowAny,),
    authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication],
)
urlpatterns = [
    # Rutas para la documentación
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

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
]
