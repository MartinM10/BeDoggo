from django.urls import path
from .views import register_view, login_view, profile_view, add_pet_view, edit_pet_view, delete_pet_view, \
    dashboard_view
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
    path('profile/', profile_view, name='user-profile'),
    path('add-pet/', add_pet_view, name='add-pet'),
    path('edit-pet/<int:pet_id>/', edit_pet_view, name='edit-pet'),
    path('delete-pet/<int:pet_id>/', delete_pet_view, name='delete-pet'),
]
