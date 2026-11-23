from django.urls import path

from . import views

app_name = "routine_tracker"

urlpatterns = [
    path("", views.tracker_view, name="tracker"),
    path("log/", views.log_view, name="log"),
]
