from django.urls import path
from .views import product_list_view, add_product_view

app_name = "product_library"

urlpatterns = [
    path("", product_list_view, name="list"),
    path("add/", add_product_view, name="add"),
]
