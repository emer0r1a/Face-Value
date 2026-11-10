from django.contrib.auth.models import User
from django.db import models

from apps.product_library.models import Product


class Routine(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="routines"
    )
    routine_name = models.CharField(max_length=100)
    routine_type = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        default="active"
    )

    def __str__(self):
        return self.routine_name


class RoutineItem(models.Model):
    routine = models.ForeignKey(
        Routine,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="routine_items"
    )
    step_number = models.PositiveIntegerField()
    step_name = models.CharField(max_length=50)

    class Meta:
        ordering = ["step_number"]

    def __str__(self):
        return f"{self.routine} - {self.product}"


class RoutineSchedule(models.Model):
    routine = models.ForeignKey(
        Routine,
        on_delete=models.CASCADE,
        related_name="schedules"
    )
    day_of_week = models.CharField(max_length=10)
    scheduled_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.routine} - {self.day_of_week}"