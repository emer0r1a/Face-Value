"""
URL configuration for face_value project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings

from apps.product_library.media_views import serve_media

from .views import landing_view

admin.site.site_header = "Face Value admin"
admin.site.site_title = "Face Value"
admin.site.index_title = "Catalog, ingredients and reports"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", include("apps.login.urls")),
    path("register/", include("apps.register.urls")),
    path("home/", include("apps.home.urls")),
    path("profile/", include("apps.user_profile.urls")),
    path("settings/", include("apps.user_settings.urls")),
    path("products/", include("apps.product_library.urls")),
    path("routines/", include("apps.routine_builder.urls")),
    path("ingredients/", include("apps.ingredient_checker.urls")),
    path("tracker/", include("apps.routine_tracker.urls")),
    path("notifications/", include("apps.notifications.urls")),

    # uploaded photos, read from the database (see apps/product_library/storage.py)
    re_path(r"^%s(?P<name>.+)$" % settings.MEDIA_URL.lstrip("/"), serve_media, name="media"),

    path("", landing_view, name="landing"),
]
