from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from beDoggo.views import index_view, lost_pets_map_view, lost_pets_data_view

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/', include('api.urls')),
                  path('', index_view, name='index'),
                  path('accounts/', include('beDoggo.urls')),
                  path('lost-pets-map/', lost_pets_map_view, name='lost-pets-map'),
                  path('lost-pets-data/', lost_pets_data_view, name='lost-pets-data'),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
