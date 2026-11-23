from django.contrib import admin

from .models import IngredientAlert, IngredientInteraction


@admin.register(IngredientInteraction)
class IngredientInteractionAdmin(admin.ModelAdmin):
    list_display = ("ingredient_1", "ingredient_2", "severity")
    list_filter = ("severity",)
    search_fields = ("ingredient_1__ingredient_name", "ingredient_2__ingredient_name")
    autocomplete_fields = ["ingredient_1", "ingredient_2"]


@admin.register(IngredientAlert)
class IngredientAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "routine", "interaction", "severity", "is_read", "created_at")
    list_filter = ("severity", "is_read")
    search_fields = ("user__username", "routine__routine_name")
