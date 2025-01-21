from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from beDoggo.views import index_view, lost_pets_map_view, mapa_perros_perdidos

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/', include('api.urls')),
                  path('', index_view, name='index'),
                  # Redirige a la página de login
                  path('accounts/', include('beDoggo.urls')),
                  path("mapa/", mapa_perros_perdidos, name="mapa_perros_perdidos"),
                  path('lost-pets-map/', lost_pets_map_view, name='lost-pets-map'),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
