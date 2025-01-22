from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Pet, Location
from .serializers import UserSerializer, RegisterSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, PetForm
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.http import JsonResponse


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user": UserSerializer(user).data,
                "message": "User registered successfully."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('user-profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('user-profile')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required
def add_pet_view(request):
    if request.method == 'POST':
        form = PetForm(request.POST)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            return redirect('dashboard')
    return render(request, 'pets/add_pet.html', {'form': PetForm()})


@login_required
def edit_pet_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        form = PetForm(request.POST, instance=pet)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = PetForm(instance=pet)
    return render(request, 'pets/edit_pet.html', {'form': form, 'pet': pet})


@login_required
def delete_pet_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        pet.delete()
        return redirect('dashboard')
    return redirect('dashboard')


@login_required
def dashboard_view(request):
    pets = Pet.objects.filter(owner=request.user)
    return render(request, 'dashboard.html', {'user': request.user, 'pets': pets})


def index_view(request):
    if request.user.is_authenticated:
        pets = Pet.objects.filter(owner=request.user)
        form = PetForm()
        return render(request, 'dashboard.html', {'user': request.user, 'pets': pets, 'form': form})
    else:
        return render(request, 'index.html')


def lost_pets_map_view(request):
    return render(request, "pets/lost_pets_map.html")


def lost_pets_data_view(request):
    latitude = float(request.GET.get('latitude', 0))
    longitude = float(request.GET.get('longitude', 0))
    distance = float(request.GET.get('distance', 5))  # Distancia en km

    # Coordenadas del usuario
    user_location = Point(longitude, latitude, srid=4326)

    # Filtrar mascotas perdidas dentro de la distancia especificada
    lost_pets = Pet.objects.filter(
        is_lost=True,
        locations__location__distance_lte=(user_location, D(km=distance))
    ).annotate(distance=Distance('locations__location', user_location)).select_related('owner')

    locations = [
        {
            'name': pet.name,
            'breed': pet.breed,
            'age': pet.age,
            'latitude': pet.locations.first().location.y,
            'longitude': pet.locations.first().location.x,
            'owner_name': f"{pet.owner.first_name} {pet.owner.last_name}",
            'owner_phone': pet.owner.phone if pet.owner.phone else "N/A",
            'owner_email': pet.owner.email if pet.owner.email else "N/A",
        }
        for pet in lost_pets
    ]

    return JsonResponse({'locations': locations})
