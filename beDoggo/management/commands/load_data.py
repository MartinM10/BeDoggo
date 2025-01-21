from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from beDoggo.models import User, Pet, Location


class Command(BaseCommand):
    help = "Carga datos iniciales en la base de datos"

    def handle(self, *args, **kwargs):
        # Crear usuarios
        user1, created1 = User.objects.get_or_create(
            username="user1",
            defaults={
                "email": "user1@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "address": "Calle Principal 123",
                "phone": "123456789",
                "on_boarding": True,
            }
        )
        if created1:
            user1.set_password("password123")  # Hashea la contraseña
            user1.save()  # Guarda los cambios en la base de datos

        user2, created2 = User.objects.get_or_create(
            username="user2",
            defaults={
                "email": "user2@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "address": "Avenida Central 456",
                "phone": "987654321",
                "on_boarding": False,
            }
        )
        if created2:
            user2.set_password("password123")  # Hashea la contraseña
            user2.save()  # Guarda los cambios en la base de datos

        self.stdout.write(self.style.SUCCESS("Usuarios creados con éxito."))

        # Crear mascotas
        pet1, created_pet1 = Pet.objects.get_or_create(
            name="Bobby",
            defaults={
                "breed": "Golden Retriever",
                "age": 3,
                "observations": "Es muy amigable.",
                "is_lost": True,
                "owner": user1,
            }
        )
        pet2, created_pet2 = Pet.objects.get_or_create(
            name="Misty",
            defaults={
                "breed": "Persian Cat",
                "age": 2,
                "observations": "Le gusta dormir.",
                "is_lost": True,
                "owner": user2,
            }
        )

        if created_pet1 and created_pet2:
            self.stdout.write(self.style.SUCCESS("Mascotas creadas con éxito."))
        else:
            self.stdout.write(self.style.WARNING("Algunas mascotas ya existían."))

        # Crear ubicaciones usando PointField
        location1, created_loc1 = Location.objects.get_or_create(
            location=Point(-4.435477, 36.709157), pet=pet1
        )
        location2, created_loc2 = Location.objects.get_or_create(
            location=Point(-4.433629, 36.709964), pet=pet2
        )
        location3, created_loc3 = Location.objects.get_or_create(
            location=Point(-4.441132, 36.709292), pet=pet1
        )

        if created_loc1 or created_loc2 or created_loc3:
            self.stdout.write(self.style.SUCCESS("Ubicaciones creadas con éxito."))
        else:
            self.stdout.write(self.style.WARNING("Algunas ubicaciones ya existían."))

        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados correctamente."))
