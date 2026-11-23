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
    search_fields = ("product__product_name", "description", "user__username")
    readonly_fields = ("reported_at", "resolved_at")
    actions = ["mark_resolved", "mark_dismissed"]

    def _close(self, request, queryset, status):
        """Close open reports and notify each reporter via the notification service."""
        from apps.notifications.service import notify_report_update

        now = timezone.now()
        count = 0
        for report in queryset.exclude(status=status):
            report.status, report.resolved_at = status, now
            report.save(update_fields=["status", "resolved_at"])
            notify_report_update(report)
            count += 1
        self.message_user(request, f"{count} report(s) updated and the reporters notified.")

    @admin.action(description="Mark selected reports as resolved")
    def mark_resolved(self, request, queryset):
        self._close(request, queryset, "resolved")

    @admin.action(description="Dismiss selected reports (no change needed)")
    def mark_dismissed(self, request, queryset):
        self._close(request, queryset, "dismissed")


admin.site.register(ProductIngredient)
admin.site.register(ProductHistory)
