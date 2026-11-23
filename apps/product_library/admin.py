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

    def _close(self, request, queryset, status, title, message):
        """Close open reports and let each reporter know in their bell."""
        from apps.notifications.models import Notification

        now = timezone.now()
        count = 0
        for report in queryset.exclude(status=status):
            report.status, report.resolved_at = status, now
            report.save(update_fields=["status", "resolved_at"])
            Notification.objects.create(
                user=report.user, title=title,
                message=message.format(product=report.product.product_name),
                notification_type="report", scheduled_at=now,
            )
            count += 1
        self.message_user(request, f"{count} report(s) updated and the reporters notified.")

    @admin.action(description="Mark selected reports as resolved")
    def mark_resolved(self, request, queryset):
        self._close(request, queryset, "resolved", "Your report was resolved",
                    "Thanks for flagging {product}. The details have been looked at.")

    @admin.action(description="Dismiss selected reports (no change needed)")
    def mark_dismissed(self, request, queryset):
        self._close(request, queryset, "dismissed", "Your report was reviewed",
                    "We looked at your report on {product} and didn't need to change anything.")


admin.site.register(ProductIngredient)
admin.site.register(ProductHistory)
