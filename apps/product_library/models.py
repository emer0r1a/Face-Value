from django.contrib.auth.models import User
from django.db import models


class Product(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="products"
    )
    product_name = models.CharField(max_length=150)
    brand = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="active")

    def __str__(self):
        return f"{self.brand} - {self.product_name}"


class Ingredient(models.Model):
    ingredient_name = models.CharField(
        max_length=100,
        unique=True
    )
    function = models.CharField(max_length=150)
    description = models.TextField()
    caution = models.TextField(blank=True)

    def __str__(self):
        return self.ingredient_name


class ProductIngredient(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_ingredients"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="product_ingredients"
    )
    ingredient_order = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "ingredient"],
                name="unique_product_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.product} - {self.ingredient}"


class ProductHistory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="history"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="product_history"
    )
    action = models.CharField(max_length=30)
    action_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product} - {self.action}"


class ProductReport(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reports"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="product_reports"
    )
    reason = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        default="pending"
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Report for {self.product}"