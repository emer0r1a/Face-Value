from django.contrib import admin
from django.utils import timezone

from .models import (
    Ingredient,
    Product,
    ProductHistory,
    ProductIngredient,
    ProductReport,
)


class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 0
    autocomplete_fields = ["ingredient"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_name", "brand", "category", "user", "status", "date_added")
    list_filter = ("category", "status")
    search_fields = ("product_name", "brand", "user__username")
    inlines = [ProductIngredientInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("ingredient_name", "function", "has_caution")
    search_fields = ("ingredient_name", "function")
    list_filter = ("function",)

    @admin.display(boolean=True, description="Caution")
    def has_caution(self, obj):
        return bool(obj.caution)


@admin.register(ProductReport)
class ProductReportAdmin(admin.ModelAdmin):
    list_display = ("product", "reason", "user", "status", "reported_at")
    list_filter = ("status", "reason")
    search_fields = ("product__product_name", "description")
    actions = ["mark_resolved"]

    @admin.action(description="Mark selected reports as resolved")
    def mark_resolved(self, request, queryset):
        queryset.exclude(status="resolved").update(
            status="resolved", resolved_at=timezone.now()
        )


admin.site.register(ProductIngredient)
admin.site.register(ProductHistory)
