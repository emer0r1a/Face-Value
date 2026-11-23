from django.urls import path

from .views import password_view, profile_view

app_name = "user_profile"

urlpatterns = [
    path("", profile_view, name="profile"),
    path("password/", password_view, name="password"),
]
