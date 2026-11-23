from django.urls import path

from . import views

app_name = "product_library"

urlpatterns = [
    path("", views.product_list_view, name="list"),
    path("add/", views.add_product_view, name="add"),
    path("<int:pk>/", views.product_detail_view, name="detail"),
    path("<int:pk>/edit/", views.edit_product_view, name="edit"),
    path("<int:pk>/delete/", views.delete_product_view, name="delete"),
    path("<int:pk>/status/", views.toggle_status_view, name="status"),
    path("<int:pk>/report/", views.report_product_view, name="report"),
    path("<int:pk>/open/", views.open_product_view, name="open"),
    path("<int:pk>/finish/", views.finish_product_view, name="finish"),
    path("<int:pk>/restock/", views.restock_product_view, name="restock"),
    path("shopping/", views.shopping_view, name="shopping"),
]
