from django.contrib.auth.models import User
from django.db import models

from apps.product_library.models import Ingredient
from apps.routine_builder.models import Routine


class IngredientInteraction(models.Model):
    ingredient_1 = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="interactions_as_first"
    )
    ingredient_2 = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="interactions_as_second"
    )
    severity = models.CharField(max_length=20)
    warning_message = models.TextField()
    recommendation = models.TextField(blank=True)

    def __str__(self):
        return f"{self.ingredient_1} + {self.ingredient_2}"


class IngredientAlert(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ingredient_alerts"
    )
    routine = models.ForeignKey(
        Routine,
        on_delete=models.CASCADE,
        related_name="ingredient_alerts"
    )
    interaction = models.ForeignKey(
        IngredientInteraction,
        on_delete=models.CASCADE,
        related_name="alerts"
    )
    alert_message = models.TextField()
    severity = models.CharField(max_length=20)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.severity} - {self.user.username}"