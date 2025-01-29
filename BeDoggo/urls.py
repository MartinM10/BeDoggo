from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from beDoggo.views import index_view, lost_pets_map_view, lost_pets_data_view, search_pet_view, add_medical_record_view, \
    register_veterinarian_view, dashboard_view

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/', include('api.urls')),
                  # path('', index_view, name='index'),
                  path('', dashboard_view, name='index'),
                  path('accounts/', include('beDoggo.urls')),
                  path('lost-pets-map/', lost_pets_map_view, name='lost-pets-map'),
                  path('lost-pets-data/', lost_pets_data_view, name='lost-pets-data'),
                  path('veterinarians/search/', search_pet_view, name='search-pet'),
                  path('veterinarians/add-medical-record/<int:pet_id>/', add_medical_record_view,
                       name='add-medical-record'),
                  path('register-veterinarian/', register_veterinarian_view, name='register-veterinarian'),
                  path('dashboard/', dashboard_view, name='dashboard'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:  # Solo habilitar servir archivos de medios en modo DEBUG
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
