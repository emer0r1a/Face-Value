from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render
from django.urls import reverse

from apps.product_library.models import Ingredient, Product, ProductIngredient
from apps.product_library.views import art_for
from apps.routine_builder.models import Routine, RoutineItem

from .models import IngredientInteraction
from .services import group_for, group_payload, is_classified


@login_required
def hub_view(request):
    """Ingredient Checker & Guide Hub.

    All the data the page needs is sent once as JSON, so picking items and
    searching the guide react instantly without extra requests. Only the
    signed-in user's own products and routines are included.
    """
    user = request.user

    ingredients = list(Ingredient.objects.order_by("ingredient_name"))
    ingredient_data = [{
        "id": i.pk,
        "name": i.ingredient_name,
        "function": i.function,
        "description": i.description,
        "caution": i.caution,
        "group": group_for(i.function),
        "classified": is_classified(i),
    } for i in ingredients]

    interactions = [{
        "a": it.ingredient_1_id,
        "b": it.ingredient_2_id,
        "severity": it.severity.lower(),
        "message": it.warning_message,
        "tip": it.recommendation,
    } for it in IngredientInteraction.objects.all()]

    products = list(
        Product.objects.filter(user=user, status="active")
        .prefetch_related(Prefetch(
            "product_ingredients",
            queryset=ProductIngredient.objects.order_by("ingredient_order"),
        ))
        .order_by("product_name")
    )
    product_data = [{
        "id": p.pk,
        "name": p.product_name,
        "brand": p.brand,
        "category": p.category,
        "art": art_for(p.category),
        "image": p.image.url if p.image else "",
        "url": reverse("product_library:detail", args=[p.pk]),
        "ingredients": [pi.ingredient_id for pi in p.product_ingredients.all()],
    } for p in products]

    active_ids = {p.pk for p in products}
    routines = (
        Routine.objects.filter(user=user, status="active")
        .prefetch_related(Prefetch("items", queryset=RoutineItem.objects.order_by("step_number")))
        .order_by("routine_name")
    )
    routine_data = []
    for r in routines:
        ids = []
        for it in r.items.all():
            if it.product_id in active_ids and it.product_id not in ids:
                ids.append(it.product_id)
        if ids:
            routine_data.append({"id": r.pk, "name": r.routine_name, "type": r.routine_type.lower(), "products": ids})

    return render(request, "ingredient_checker/ingredient_hub.html", {
        "hub_data": {
            "ingredients": ingredient_data,
            "interactions": interactions,
            "groups": group_payload(),
            "products": product_data,
            "routines": routine_data,
        },
        "ingredient_total": sum(1 for i in ingredient_data if i["classified"]),
        "clash_total": len(interactions),
        "product_total": len(product_data),
        "add_product_url": reverse("product_library:add"),
    })
