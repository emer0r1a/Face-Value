from django.urls import path

from . import views

app_name = "ingredient_checker"

urlpatterns = [
    path("", views.hub_view, name="hub"),
]
