from django.contrib import admin
from .models import User, Veterinarian, Pet, MedicalRecord, Location, AccessCode, GPSDevice

admin.site.register(User)
admin.site.register(Veterinarian)
admin.site.register(Pet)
admin.site.register(MedicalRecord)
admin.site.register(Location)
admin.site.register(AccessCode)
admin.site.register(GPSDevice)
