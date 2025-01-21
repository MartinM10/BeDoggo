from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point

from beDoggo.models import User, Pet, Location


class Command(BaseCommand):
    help = "Carga datos iniciales en la base de datos"

    def handle(self, *args, **kwargs):
        # Crear usuarios
        user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            address="Calle Principal 123",
            phone="123456789",
            on_boarding=True
        )
        user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123",
            first_name="Jane",
            last_name="Smith",
            address="Avenida Central 456",
            phone="987654321",
            on_boarding=False
        )

        self.stdout.write(self.style.SUCCESS("Usuarios creados con éxito."))

        # Crear mascotas
        pet1 = Pet.objects.create(
            name="Bobby",
            breed="Golden Retriever",
            age=3,
            observations="Es muy amigable.",
            is_lost=True,
            owner=user1
        )
        pet2 = Pet.objects.create(
            name="Misty",
            breed="Persian Cat",
            age=2,
            observations="Le gusta dormir.",
            is_lost=True,
            owner=user2
        )

        self.stdout.write(self.style.SUCCESS("Mascotas creadas con éxito."))

        # Crear ubicaciones usando PointField
        Location.objects.create(location=Point(-4.435477, 36.709157), pet=pet1)
        Location.objects.create(location=Point(-4.433629, 36.709964), pet=pet2)
        Location.objects.create(location=Point(-4.441132, 36.709292), pet=pet1)

        self.stdout.write(self.style.SUCCESS("Ubicaciones creadas con éxito."))

        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados correctamente."))
