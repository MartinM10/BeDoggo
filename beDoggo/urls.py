from django.urls import path
from .views import register_view, login_view, profile_view
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
    path('profile/', profile_view, name='user-profile'),
]
