from django.contrib import admin

from .models import RoutineLog


@admin.register(RoutineLog)
class RoutineLogAdmin(admin.ModelAdmin):
    list_display = ("routine", "user", "log_date", "status", "completed_at")
    list_filter = ("status", "log_date")
    search_fields = ("routine__routine_name", "user__username")
    date_hierarchy = "log_date"
