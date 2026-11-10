import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, Q
from django.shortcuts import redirect, render

from .models import Ingredient, Product, ProductHistory, ProductIngredient

# Category is a free CharField in the model, so the dropdown options live here.
CATEGORIES = [
    "Cleanser",
    "Toner",
    "Serum",
    "Moisturizer",
    "Sunscreen",
    "Exfoliant",
    "Mask",
    "Eye Care",
    "Treatment",
    "Other",
]


def parse_ingredients(raw_text):
    """Split 'Water, Glycerin, Niacinamide' (commas or new lines) into a
    clean list, keeping order and removing case-insensitive duplicates."""
    seen = set()
    names = []
    for part in re.split(r"[,\n]", raw_text):
        name = " ".join(part.split())
        if name and name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    return names


@login_required
def product_list_view(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    products = (
        Product.objects.filter(user=request.user)
        .prefetch_related(
            Prefetch(
                "product_ingredients",
                queryset=ProductIngredient.objects
                .select_related("ingredient")
                .order_by("ingredient_order"),
            )
        )
        .order_by("-date_added")
    )

    if query:
        products = products.filter(
            Q(product_name__icontains=query)
            | Q(brand__icontains=query)
            | Q(description__icontains=query)
            | Q(product_ingredients__ingredient__ingredient_name__icontains=query)
        ).distinct()

    if category:
        products = products.filter(category__iexact=category)

    # Only offer categories the user actually has products in
    user_categories = (
        Product.objects.filter(user=request.user)
        .order_by("category")
        .values_list("category", flat=True)
        .distinct()
    )

    return render(request, "product_library/product_library.html", {
        "products": products,
        "categories": user_categories,
        "query": query,
        "selected_category": category,
        "total_count": Product.objects.filter(user=request.user).count(),
    })


@login_required
def add_product_view(request):
    context = {"categories": CATEGORIES, "values": {}}

    if request.method == "POST":
        product_name = request.POST.get("product_name", "").strip()
        brand = request.POST.get("brand", "").strip()
        category = request.POST.get("category", "").strip()
        description = request.POST.get("description", "").strip()
        ingredients_raw = request.POST.get("ingredients", "")

        context["values"] = {
            "product_name": product_name,
            "brand": brand,
            "category": category,
            "description": description,
            "ingredients": ingredients_raw,
        }

        ingredient_names = parse_ingredients(ingredients_raw)

        error = None
        if not product_name or not brand or not category:
            error = "Product name, brand, and category are required."
        elif len(product_name) > 150:
            error = "Product name must be 150 characters or fewer."
        elif len(brand) > 100:
            error = "Brand must be 100 characters or fewer."
        elif category not in CATEGORIES:
            error = "Please choose a valid category."
        elif any(len(n) > 100 for n in ingredient_names):
            error = "Each ingredient name must be 100 characters or fewer."

        if error:
            context["error"] = error
            return render(request, "product_library/add_product.html", context)

        with transaction.atomic():
            product = Product.objects.create(
                user=request.user,
                product_name=product_name,
                brand=brand,
                category=category,
                description=description,
            )

            for order, name in enumerate(ingredient_names, start=1):
                ingredient = Ingredient.objects.filter(
                    ingredient_name__iexact=name
                ).first()

                if ingredient is None:
                    # Unknown ingredient: add a placeholder entry to the shared
                    # ingredient table so it can be filled in later.
                    ingredient = Ingredient.objects.create(
                        ingredient_name=name,
                        function="Not yet classified",
                        description="No description available yet.",
                    )

                ProductIngredient.objects.create(
                    product=product,
                    ingredient=ingredient,
                    ingredient_order=order,
                )

            ProductHistory.objects.create(
                product=product,
                user=request.user,
                action="added",
                notes="Product added to library.",
            )

        messages.success(request, f"“{product.product_name}” was added to your library.")
        return redirect("product_library:list")

    return render(request, "product_library/add_product.html", context)
