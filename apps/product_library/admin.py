from django.contrib import admin

from .models import (
    Ingredient,
    Product,
    ProductHistory,
    ProductIngredient,
    ProductReport,
)

admin.site.register(Product)
admin.site.register(Ingredient)
admin.site.register(ProductIngredient)
admin.site.register(ProductHistory)
admin.site.register(ProductReport)
