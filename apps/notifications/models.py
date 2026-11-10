from django.contrib.auth.models import User
from django.db import models

from apps.routine_builder.models import Routine


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    routine = models.ForeignKey(
        Routine,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=30)
    scheduled_at = models.DateTimeField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.title