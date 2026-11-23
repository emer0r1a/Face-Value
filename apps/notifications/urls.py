from django.urls import path

from .views import dismiss_view, inbox_view, mark_all_read_view, mark_read_view, poll_view

app_name = "notifications"

urlpatterns = [
    path("",                     inbox_view,       name="inbox"),
    path("<int:pk>/dismiss/",    dismiss_view,     name="dismiss"),
    path("<int:pk>/read/",       mark_read_view,   name="read"),
    path("mark-all-read/",       mark_all_read_view, name="mark_all_read"),
    path("poll/",                poll_view,        name="poll"),
]
