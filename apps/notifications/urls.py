from django.urls import path

from .views import dismiss_view

app_name = "notifications"

urlpatterns = [
    path("<int:pk>/dismiss/", dismiss_view, name="dismiss"),
]
