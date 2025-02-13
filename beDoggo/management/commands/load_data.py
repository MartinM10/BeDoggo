import random
import string
import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from beDoggo.models import User, GPSDevice, Pet, Location, SexUserChoices, SexPetChoices


def generate_device_code():
    """Genera un código único de 6 caracteres alfanuméricos."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_access_code():
    """Genera un código de acceso de 10 caracteres alfanuméricos."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


def generate_malaga_coordinates():
    """Genera coordenadas aleatorias dentro de la provincia de Málaga."""
    latitude = round(random.uniform(36.5, 36.9), 6)  # Latitud dentro de Málaga
    longitude = round(random.uniform(-4.9, -4.2), 6)  # Longitud dentro de Málaga
    return latitude, longitude


class Command(BaseCommand):
    help = "Carga datos ficticios para simular la adopción de la aplicación."

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=200, help='Número de usuarios a crear (default: 200)')
        parser.add_argument('--pets_per_user', type=int, default=3,
                            help='Número máximo de mascotas por usuario (default: 3)')
        parser.add_argument('--locations', type=int, default=5,
                            help='Número de localizaciones a generar por dispositivo en caso de mascota perdida (default: 5)')

    def handle(self, *args, **options):
        fake = Faker()
        total_users = options['users']
        max_pets = options['pets_per_user']
        locations_per_device = options['locations']

        self.stdout.write(self.style.MIGRATE_HEADING("Iniciando carga de datos ficticios..."))
        start_time = time.time()

        created_users = []

        with transaction.atomic():
            for i in range(1, total_users + 1):
                email = f'user{i}@example.com'
                user = User.objects.create(
                    email=email,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    profile_picture=fake.image_url(),
                    email_verified=fake.boolean(25),
                    address=fake.address(),
                    prefix_phone=fake.country_calling_code(),
                    phone=fake.phone_number()[:20],
                    sex=random.choice([choice[0] for choice in SexUserChoices.choices]),
                    acquisition_channel=random.choice([choice[0] for choice in User.AcquisitionChannelChoices.choices]),
                    birth_date=fake.date_of_birth(minimum_age=18, maximum_age=80),
                    onboarding_completed=random.choice([True, False]),
                )
                user.set_password('password123')
                user.save()
                created_users.append(user)

                num_pets = random.randint(1, max_pets)
                for _ in range(num_pets):
                    pet = Pet.objects.create(
                        name=fake.first_name(),
                        sex=random.choice([choice[0] for choice in SexPetChoices.choices]),
                        breed=fake.word().capitalize(),
                        color=fake.color_name(),
                        birth_date=fake.date_of_birth(minimum_age=0, maximum_age=20),
                        weight=round(random.uniform(1.0, 50.0), 2),
                        chip_number=fake.unique.bothify(text='??##??##'),
                        observations=fake.text(max_nb_chars=200),
                        sterilized=random.choice([True, False]),
                        is_lost=False,
                        phone_emergency=fake.phone_number()[:20],
                        owner=user,
                        image=fake.image_url(),
                    )

                    if random.random() < 0.2:
                        pet.is_lost = True
                        pet.save()

                        gps_device = GPSDevice.objects.create(
                            code=generate_device_code(),
                            is_active=True,
                            activated_at=timezone.now(),
                        )
                        pet.gps_device = gps_device
                        pet.save()

                        for _ in range(locations_per_device):
                            latitude, longitude = generate_malaga_coordinates()
                            Location.objects.create(
                                gps_device=gps_device,
                                location=f"SRID=4326;POINT({longitude} {latitude})",
                                timestamp=timezone.now()
                            )

                    # Compartir mascotas con otros usuarios aleatoriamente
                    if random.random() < 0.1 and len(created_users) > 1:
                        shared_with = random.choice(created_users[:-1])
                        pet.shared_with.add(shared_with)

                if i % max(1, total_users // 20) == 0 or i == total_users:
                    percentage = (i / total_users) * 100
                    elapsed = time.time() - start_time
                    self.stdout.write(
                        f"Progreso: {i}/{total_users} usuarios ({percentage:.0f}%) - Tiempo transcurrido: {elapsed:.1f} s")

        total_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(f"Datos cargados exitosamente. Total de usuarios creados: {len(created_users)}."))
        self.stdout.write(self.style.SUCCESS(f"Tiempo total de ejecución: {total_time:.1f} s"))
