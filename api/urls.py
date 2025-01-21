from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PetListCreateView, PetDetailView, LocationListCreateView, LocationDetailView, \
    PetAccessListCreateView, PetAccessDetailView, GoogleLoginView

urlpatterns = [
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
