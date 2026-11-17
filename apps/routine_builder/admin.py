from django.contrib import admin

from .models import Routine, RoutineItem, RoutineSchedule


class RoutineItemInline(admin.TabularInline):
    model = RoutineItem
    extra = 0
    autocomplete_fields = ["product"]


class RoutineScheduleInline(admin.TabularInline):
    model = RoutineSchedule
    extra = 0


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ("routine_name", "routine_type", "user", "status", "created_at")
    list_filter = ("routine_type", "status")
    search_fields = ("routine_name", "user__username")
    inlines = [RoutineItemInline, RoutineScheduleInline]
