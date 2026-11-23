from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from apps.routine_builder.models import Routine


class Notification(models.Model):
    # Notification types
    TYPE_REPORT_UPDATE   = "report_update"
    TYPE_EXPIRY_SOON     = "expiry_soon"
    TYPE_EXPIRY_EXPIRED  = "expiry_expired"
    TYPE_STREAK          = "streak"
    TYPE_ROUTINE_REMIND  = "routine_remind"
    TYPE_WELCOME         = "welcome"
    TYPE_GENERAL         = "general"

    TYPE_CHOICES = [
        (TYPE_REPORT_UPDATE,  "Report update"),
        (TYPE_EXPIRY_SOON,    "Expiry soon"),
        (TYPE_EXPIRY_EXPIRED, "Expired product"),
        (TYPE_STREAK,         "Streak"),
        (TYPE_ROUTINE_REMIND, "Routine reminder"),
        (TYPE_WELCOME,        "Welcome"),
        (TYPE_GENERAL,        "General"),
    ]

    ICON_MAP = {
        TYPE_REPORT_UPDATE:  "📋",
        TYPE_EXPIRY_SOON:    "⏳",
        TYPE_EXPIRY_EXPIRED: "🗑️",
        TYPE_STREAK:         "🔥",
        TYPE_ROUTINE_REMIND: "🌿",
        TYPE_WELCOME:        "👋",
        TYPE_GENERAL:        "🔔",
    }

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    routine = models.ForeignKey(
        Routine, on_delete=models.CASCADE,
        related_name="notifications", null=True, blank=True
    )
    title            = models.CharField(max_length=150)
    message          = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_GENERAL)
    url              = models.CharField(max_length=300, blank=True, default="")
    icon             = models.CharField(max_length=20, blank=True, default="")
    scheduled_at     = models.DateTimeField(default=timezone.now)
    created_at       = models.DateTimeField(default=timezone.now)
    is_read          = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def display_icon(self):
        return self.icon or self.ICON_MAP.get(self.notification_type, "🔔")