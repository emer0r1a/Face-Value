from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "has_photo")
    search_fields = ("user__username", "user__email", "full_name")

    @admin.display(boolean=True, description="Photo")
    def has_photo(self, obj):
        return bool(obj.profile_image)
