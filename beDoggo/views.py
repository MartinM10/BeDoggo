from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Pet, Location, User
from .serializers import UserSerializer, RegisterSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, PetForm, MedicalRecordForm, ProfileForm, VeterinarianRegistrationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.http import JsonResponse
from django.db.models import Q


def is_veterinarian(user):
    return user.is_authenticated and hasattr(user, 'veterinarian_profile')


@user_passes_test(is_veterinarian)
@login_required
def search_pet_view(request):
    pets = None
    query = request.GET.get('query', '')

    if query:
        pets = Pet.objects.filter(
            Q(owner__email__icontains=query) | Q(chip_number__icontains=query)
        ).select_related('owner')

    return render(request, 'veterinarians/search_pet.html', {'pets': pets, 'query': query})


@login_required
@user_passes_test(is_veterinarian)
def add_medical_record_view(request, pet_uuid):
    pet = get_object_or_404(Pet, uuid=pet_uuid)
    if request.method == "POST":
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.pet = pet
            medical_record.veterinarian = request.user.veterinarian_profile
            medical_record.save()
            return redirect('search-pet')
    else:
        form = MedicalRecordForm()
    return render(request, 'veterinarians/add_medical_record.html', {'form': form, 'pet': pet})


@login_required
@user_passes_test(is_veterinarian)
def view_medical_records(request, pet_uuid):
    pet = get_object_or_404(Pet, uuid=pet_uuid)
    medical_records = pet.medical_records.all().order_by('-date')

    return render(request, 'veterinarians/view_medical_records.html',
                  {'pet': pet, 'medical_records': medical_records})


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
    profile = get_object_or_404(User, id=request.user.id)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('user-profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


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
def edit_pet_view(request, pet_uuid):
    pet = get_object_or_404(Pet, uuid=pet_uuid)

    # Asegurarse de que el usuario sea el dueño de la mascota o un veterinario
    if request.user != pet.owner and not is_veterinarian(request.user):
        return redirect('dashboard')  # Redirige si no tiene permiso

    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            # Redirige dependiendo del rol
            if request.user == pet.owner:
                return redirect('dashboard')  # Página para dueños de mascotas
            elif is_veterinarian(request.user):
                return redirect('dashboard')  # Página para veterinarios
    else:
        form = PetForm(instance=pet)

    return render(request, 'pets/edit_pet.html', {'form': form, 'pet': pet})


@login_required
def delete_pet_view(request, pet_uuid):
    pet = get_object_or_404(Pet, uuid=pet_uuid, owner=request.user)
    if request.method == 'POST':
        pet.delete()
        return redirect('dashboard')
    return redirect('dashboard')


"""
@login_required
def dashboard_view(request):
    pets = Pet.objects.filter(owner=request.user)
    return render(request, 'dashboard.html', {'user': request.user, 'pets': pets})
"""


@login_required
def dashboard_view(request):
    pets = Pet.objects.filter(owner=request.user)
    # user_is_veterinarian = True if request.user.veterinarian_profile else None
    return render(request, 'dashboard.html', {
        'user': request.user,
        'pets': pets,
        'is_veterinarian': is_veterinarian(user=request.user)  # Pasar esta información al template
    })


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


"""
def add_medical_record(request):
    if request.method == "POST":
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('pet_detail', pk=form.cleaned_data['pet'].id)  # Cambia 'pet_detail' por tu vista
    else:
        form = MedicalRecordForm()

    return render(request, 'veterinarians/add_medical_record.html', {'form': form})
"""


def pet_detail(request, pk):
    pet = get_object_or_404(Pet, pk=pk)
    medical_records = pet.medical_records.all()  # Historial médico de la mascota
    return render(request, 'pets/pet_detail.html', {'pet': pet, 'medical_records': medical_records})


def register_veterinarian_view(request):
    if request.method == 'POST':
        form = VeterinarianRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guardar el usuario
            # Autenticar al usuario recién creado
            user = authenticate(request, email=form.cleaned_data['email'], password=form.cleaned_data['password1'])
            if user is not None:
                login(request, user)  # Inicia sesión
                return redirect('dashboard')  # Redirige al dashboard
    else:
        form = VeterinarianRegistrationForm()
    return render(request, 'veterinarians/register_veterinarian.html', {'form': form})
