from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from beDoggo.models import User, Pet, Location, Veterinarian, GPSDevice, AccessCode, MedicalRecord


class Command(BaseCommand):
    help = "Carga datos iniciales en la base de datos"

    def handle(self, *args, **kwargs):
        # Crear usuarios
        user1, created1 = User.objects.get_or_create(
            email="user1@example.com",
            defaults={
                "username": "user1",
                "first_name": "John",
                "last_name": "Doe",
                "address": "Calle Principal 123",
                "phone": "123456789",
                "onboarding_completed": True,
            }
        )
        if created1:
            user1.set_password("password123")
            user1.save()

        user2, created2 = User.objects.get_or_create(
            email="user2@example.com",
            defaults={
                "username": "user2",
                "first_name": "Jane",
                "last_name": "Smith",
                "address": "Avenida Central 456",
                "phone": "987654321",
                "onboarding_completed": False,
            }
        )
        if created2:
            user2.set_password("password123")
            user2.save()

        self.stdout.write(self.style.SUCCESS("Usuarios creados con éxito."))

        # Crear veterinario
        vet_user, created_vet_user = User.objects.get_or_create(
            email="vet1@example.com",
            defaults={"username": "vet1", "first_name": "Dr. Albert", "last_name": "Martínez"}
        )
        if created_vet_user:
            vet_user.set_password("password123")
            vet_user.save()

        veterinarian, created_vet = Veterinarian.objects.get_or_create(
            user=vet_user,
            defaults={
                "vet_license_number": "VET12345",
                "clinic_name": "Clínica Veterinaria Los Amigos",
                "clinic_address": "Avenida Vet 789",
                "clinic_phone": "555-555-555",
                "available_hours": "9:00-18:00"
            }
        )

        self.stdout.write(self.style.SUCCESS("Veterinario creado con éxito."))

        # Crear dispositivos GPS
        gps_device1, created_gps1 = GPSDevice.objects.get_or_create(
            code="ABC123",
            defaults={"is_active": True}
        )

        gps_device2, created_gps2 = GPSDevice.objects.get_or_create(
            code="XYZ789",
            defaults={"is_active": False}
        )

        self.stdout.write(self.style.SUCCESS("Dispositivos GPS creados con éxito."))

        # Crear mascotas
        pet1, created_pet1 = Pet.objects.get_or_create(
            name="Bobby",
            defaults={
                "breed": "Golden Retriever",
                "age": 3,
                "observations": "Es muy amigable.",
                "is_lost": True,
                "owner": user1,
                "gps_device": gps_device1,
                "veterinarian": veterinarian,
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
                "gps_device": gps_device2,
            }
        )

        if created_pet1 and created_pet2:
            self.stdout.write(self.style.SUCCESS("Mascotas creadas con éxito."))
        else:
            self.stdout.write(self.style.WARNING("Algunas mascotas ya existían."))

        # Crear ubicaciones de mascotas
        location1, created_loc1 = Location.objects.get_or_create(
            location=Point(-4.435477, 36.709157), gps_device=gps_device1
        )
        location2, created_loc2 = Location.objects.get_or_create(
            location=Point(-4.433629, 36.709964), gps_device=gps_device2
        )

        if created_loc1 or created_loc2:
            self.stdout.write(self.style.SUCCESS("Ubicaciones creadas con éxito."))
        else:
            self.stdout.write(self.style.WARNING("Algunas ubicaciones ya existían."))

        # Generar código de acceso para compartir una mascota
        access_code1, created_access1 = AccessCode.objects.get_or_create(
            pet=pet1,
            created_by=user1
        )

        self.stdout.write(self.style.SUCCESS(f"Código de acceso generado: {access_code1.code[:8]}..."))

        # Crear historial médico para la mascota "Bobby"
        medical_record1, created_med1 = MedicalRecord.objects.get_or_create(
            pet=pet1,
            veterinarian=veterinarian,
            visit_reason="Vacunación anual",
            diagnosis="Salud en buen estado",
            treatment="Vacuna contra la rabia",
            medication="Ninguna",
            vaccines="Rabia, Moquillo",
            observations="No presentó reacciones adversas",
            next_visit="2025-06-10"
        )

        medical_record2, created_med2 = MedicalRecord.objects.get_or_create(
            pet=pet1,
            veterinarian=veterinarian,
            visit_reason="Revisión general",
            diagnosis="Ligera inflamación en la pata",
            treatment="Antiinflamatorio",
            medication="Meloxicam",
            observations="Debe descansar y evitar actividad intensa",
            next_visit="2025-07-05"
        )

        if created_med1 or created_med2:
            self.stdout.write(self.style.SUCCESS("Historial médico creado con éxito."))
        else:
            self.stdout.write(self.style.WARNING("El historial médico ya existía."))

        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados correctamente."))
