from django.contrib.auth.models import User
from django.db import models

from apps.routine_builder.models import Routine


class RoutineLog(models.Model):
    routine = models.ForeignKey(
        Routine,
        on_delete=models.CASCADE,
        related_name="logs"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="routine_logs"
    )
    log_date = models.DateField()
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.routine} - {self.log_date}"