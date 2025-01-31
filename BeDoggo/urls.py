from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from beDoggo.views import index_view, lost_pets_map_view, lost_pets_data_view, search_pet_view, add_medical_record_view, \
    register_veterinarian_view, dashboard_view, add_pet_view, edit_pet_view, delete_pet_view, view_medical_records

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/', include('api.urls')),
                  path('', index_view, name='index'),
                  path('dashboard', dashboard_view, name='dashboard'),
                  path('accounts/', include('beDoggo.urls')),
                  path('add-pet/', add_pet_view, name='add-pet'),
                  path('edit-pet/<uuid:pet_uuid>/', edit_pet_view, name='edit-pet'),
                  path('delete-pet/<uuid:pet_uuid>/', delete_pet_view, name='delete-pet'),
                  path('lost-pets-map/', lost_pets_map_view, name='lost-pets-map'),
                  path('lost-pets-data/', lost_pets_data_view, name='lost-pets-data'),
                  path('veterinarians/search/', search_pet_view, name='search-pet'),
                  path('veterinarians/add-medical-record/<uuid:pet_uuid>/', add_medical_record_view,
                       name='add-medical-record'),
                  path('veterinarians/view_medical_records/<uuid:pet_uuid>/', view_medical_records,
                       name='view-medical-records'),
                  path('register-veterinarian/', register_veterinarian_view, name='register-veterinarian'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:  # Solo habilitar servir archivos de medios en modo DEBUG
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
