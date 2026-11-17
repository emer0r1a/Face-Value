from django.urls import path

from . import views

app_name = "routine_builder"

urlpatterns = [
    path("", views.routine_list_view, name="list"),
    path("new/", views.routine_create_view, name="create"),
    path("clash/", views.clash_preview_view, name="clash"),
    path("<int:pk>/edit/", views.routine_edit_view, name="edit"),
    path("<int:pk>/delete/", views.routine_delete_view, name="delete"),
    path("<int:pk>/status/", views.routine_status_view, name="status"),
    path("<int:pk>/schedule/", views.schedule_toggle_view, name="schedule"),
]
