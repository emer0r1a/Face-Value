from django.urls import path

from .views import clash_check, home_view, toggle_routine

app_name = "home"

urlpatterns = [
    path("", home_view, name="home"),
    path("routine/<int:routine_id>/toggle/", toggle_routine, name="toggle_routine"),
    path("clash/", clash_check, name="clash_check"),
]
