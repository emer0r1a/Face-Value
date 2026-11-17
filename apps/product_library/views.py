import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, Q
import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from PIL import Image, ImageOps, UnidentifiedImageError

from apps.ingredient_checker.models import IngredientInteraction
from apps.routine_builder.models import RoutineItem

from .models import (
    Ingredient,
    Product,
    ProductHistory,
    ProductIngredient,
    ProductReport,
)

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


CATEGORY_ICONS = {
    "cleanser": "🫧", "toner": "💧", "serum": "🧪", "moisturizer": "🧴",
    "sunscreen": "☀️", "exfoliant": "✨", "mask": "🌿", "eye care": "👁️",
    "treatment": "🌱",
}

REPORT_REASONS = [
    "Outdated ingredient list",
    "Wrong name or brand",
    "Product was reformulated",
    "Product discontinued",
    "Missing information",
    "Other",
]


MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def _image_error(upload):
    """Return a friendly message if the upload isn't an acceptable photo."""
    if not upload:
        return None
    if upload.size > MAX_IMAGE_BYTES:
        return "Photo must be 5 MB or smaller."
    try:
        img = Image.open(upload)
        fmt = img.format
        img.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        return "That file doesn't look like a valid image."
    finally:
        upload.seek(0)
    if fmt not in ALLOWED_IMAGE_FORMATS:
        return "Please upload a JPG, PNG, WebP or GIF photo."
    return None


def _store_image(product, upload):
    """Auto-rotate, shrink and re-encode a photo (this also drops EXIF/GPS data)."""
    img = Image.open(upload)
    img = ImageOps.exif_transpose(img)
    img.thumbnail((1400, 1400))

    buf = BytesIO()
    if img.mode in ("RGBA", "LA") or "transparency" in img.info:
        img.convert("RGBA").save(buf, "PNG", optimize=True)
        ext = "png"
    else:
        img.convert("RGB").save(buf, "JPEG", quality=85, optimize=True)
        ext = "jpg"

    old = product.image.name if product.image else None
    product.image.save(f"{uuid.uuid4().hex}.{ext}", ContentFile(buf.getvalue()), save=False)
    if old:
        product.image.storage.delete(old)


def _remove_image(product):
    if product.image:
        product.image.storage.delete(product.image.name)
        product.image = ""


def icon_for(category):
    return CATEGORY_ICONS.get((category or "").lower(), "🍃")


ART_FOR = {
    "cleanser": "pump", "toner": "bottle", "serum": "dropper",
    "moisturizer": "jar", "sunscreen": "tube", "exfoliant": "jar",
    "mask": "jar", "eye care": "dropper", "treatment": "dropper",
}


def art_for(category):
    return ART_FOR.get((category or "").lower(), "bottle")


def _own_product(request, pk):
    return get_object_or_404(Product, pk=pk, user=request.user)


def _validate_product_form(product_name, brand, category, ingredient_names):
    if not product_name or not brand or not category:
        return "Product name, brand, and category are required."
    if len(product_name) > 150:
        return "Product name must be 150 characters or fewer."
    if len(brand) > 100:
        return "Brand must be 100 characters or fewer."
    if category not in CATEGORIES:
        return "Please choose a valid category."
    if any(len(n) > 100 for n in ingredient_names):
        return "Each ingredient name must be 100 characters or fewer."
    return None


def _save_ingredients(product, ingredient_names):
    """Replace a product's ingredient list, reusing shared Ingredient rows."""
    product.product_ingredients.all().delete()
    for order, name in enumerate(ingredient_names, start=1):
        ingredient = Ingredient.objects.filter(ingredient_name__iexact=name).first()
        if ingredient is None:
            # Unknown ingredient: add a placeholder entry to the shared table
            # so an admin can classify it later.
            ingredient = Ingredient.objects.create(
                ingredient_name=name,
                function="Not yet classified",
                description="No description available yet.",
            )
        ProductIngredient.objects.create(
            product=product, ingredient=ingredient, ingredient_order=order
        )


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

    products = list(products)
    for p in products:
        p.icon = icon_for(p.category)
        p.art = art_for(p.category)

    counts = {}
    for cat in Product.objects.filter(user=request.user).values_list("category", flat=True):
        counts[cat] = counts.get(cat, 0) + 1

    return render(request, "product_library/product_library.html", {
        "products": products,
        "categories": user_categories,
        "category_counts": sorted(counts.items()),
        "query": query,
        "selected_category": category,
        "total_count": Product.objects.filter(user=request.user).count(),
    })


def _form_values(request):
    return {
        "product_name": request.POST.get("product_name", "").strip(),
        "brand": request.POST.get("brand", "").strip(),
        "category": request.POST.get("category", "").strip(),
        "description": request.POST.get("description", "").strip(),
        "ingredients": request.POST.get("ingredients", ""),
    }


@login_required
def add_product_view(request):
    context = {"categories": CATEGORIES, "values": {}}

    if request.method == "POST":
        values = _form_values(request)
        context["values"] = values
        names = parse_ingredients(values["ingredients"])

        error = _validate_product_form(
            values["product_name"], values["brand"], values["category"], names
        )
        upload = request.FILES.get("image")
        error = error or _image_error(upload)
        if error:
            context["error"] = error
            return render(request, "product_library/add_product.html", context)

        with transaction.atomic():
            product = Product.objects.create(
                user=request.user,
                product_name=values["product_name"],
                brand=values["brand"],
                category=values["category"],
                description=values["description"],
            )
            _save_ingredients(product, names)
            if upload:
                _store_image(product, upload)
                product.save(update_fields=["image"])
            ProductHistory.objects.create(
                product=product, user=request.user,
                action="added", notes="Product added to library.",
            )

        messages.success(request, f"“{product.product_name}” was added to your library.")
        return redirect("product_library:detail", pk=product.pk)

    return render(request, "product_library/add_product.html", context)


@login_required
def edit_product_view(request, pk):
    product = _own_product(request, pk)
    context = {"categories": CATEGORIES, "product": product}

    if request.method == "POST":
        values = _form_values(request)
        context["values"] = values
        names = parse_ingredients(values["ingredients"])

        error = _validate_product_form(
            values["product_name"], values["brand"], values["category"], names
        )
        upload = request.FILES.get("image")
        error = error or _image_error(upload)
        if error:
            context["error"] = error
            return render(request, "product_library/add_product.html", context)

        with transaction.atomic():
            if upload:
                _store_image(product, upload)
            elif request.POST.get("remove_image") == "1":
                _remove_image(product)
            product.product_name = values["product_name"]
            product.brand = values["brand"]
            product.category = values["category"]
            product.description = values["description"]
            product.save()
            _save_ingredients(product, names)
            ProductHistory.objects.create(
                product=product, user=request.user,
                action="updated", notes="Product details edited.",
            )

        messages.success(request, "Changes saved.")
        return redirect("product_library:detail", pk=product.pk)

    context["values"] = {
        "product_name": product.product_name,
        "brand": product.brand,
        "category": product.category,
        "description": product.description,
        "ingredients": ", ".join(
            product.product_ingredients.select_related("ingredient")
            .order_by("ingredient_order")
            .values_list("ingredient__ingredient_name", flat=True)
        ),
    }
    return render(request, "product_library/add_product.html", context)


@login_required
def product_detail_view(request, pk):
    product = _own_product(request, pk)

    items = list(
        product.product_ingredients.select_related("ingredient").order_by("ingredient_order")
    )
    ingredient_ids = [i.ingredient_id for i in items]

    # Known interactions involving this product's ingredients
    mine = {i.ingredient_id: i.ingredient for i in items}
    interactions = (
        IngredientInteraction.objects
        .filter(ingredient_1__in=ingredient_ids) | IngredientInteraction.objects.filter(ingredient_2__in=ingredient_ids)
    ).select_related("ingredient_1", "ingredient_2").distinct()

    # Which of the user's other products contain the "other side" ingredient?
    others = {}
    for pi in (
        ProductIngredient.objects.filter(product__user=request.user)
        .exclude(product=product).select_related("product")
    ):
        others.setdefault(pi.ingredient_id, set()).add(pi.product)

    cautions = []
    for it in interactions:
        a, b = it.ingredient_1, it.ingredient_2
        this, other = (a, b) if a.pk in mine else (b, a)
        cautions.append({
            "this": this, "other": other,
            "severity": it.severity.lower(),
            "message": it.warning_message,
            "tip": it.recommendation,
            "owned": sorted(others.get(other.pk, []), key=lambda p: p.product_name),
        })
    order = {"high": 0, "moderate": 1, "medium": 1, "low": 2}
    # conflicts with products the user already owns come first
    cautions.sort(key=lambda c: (not c["owned"], order.get(c["severity"], 3)))

    routines = (
        RoutineItem.objects.filter(product=product, routine__user=request.user)
        .select_related("routine")
    )

    classified = sum(1 for i in items if i.ingredient.function != "Not yet classified")
    completeness = round(100 * classified / len(items)) if items else 0

    return render(request, "product_library/product_detail.html", {
        "product": product,
        "icon": icon_for(product.category),
        "art": art_for(product.category),
        "completeness": completeness,
        "classified": classified,
        "caution_count": len(cautions),
        "owned_caution_count": sum(1 for c in cautions if c["owned"]),
        "items": items,
        "cautions": cautions,
        "routine_items": routines,
        "history": product.history.order_by("-action_date")[:8],
        "reasons": REPORT_REASONS,
        "pending_reports": product.reports.filter(status="pending").count(),
    })


@login_required
@require_POST
def delete_product_view(request, pk):
    product = _own_product(request, pk)
    name = product.product_name
    _remove_image(product)
    product.delete()
    messages.success(request, f"“{name}” was removed from your library.")
    return redirect("product_library:list")


@login_required
@require_POST
def toggle_status_view(request, pk):
    product = _own_product(request, pk)
    archiving = product.status == "active"
    product.status = "archived" if archiving else "active"
    product.save(update_fields=["status"])
    ProductHistory.objects.create(
        product=product, user=request.user,
        action="archived" if archiving else "restored",
        notes="Moved off the shelf." if archiving else "Back on the shelf.",
    )
    messages.success(
        request,
        "Moved to your archive." if archiving else "Back on your active shelf.",
    )
    return redirect("product_library:detail", pk=product.pk)


@login_required
@require_POST
def report_product_view(request, pk):
    product = _own_product(request, pk)
    reason = request.POST.get("reason", "").strip()
    description = request.POST.get("description", "").strip()

    if reason not in REPORT_REASONS or not description:
        messages.error(request, "Please choose a reason and add a short note.")
        return redirect("product_library:detail", pk=product.pk)

    ProductReport.objects.create(
        product=product, user=request.user,
        reason=reason, description=description[:2000],
    )
    ProductHistory.objects.create(
        product=product, user=request.user,
        action="reported", notes=f"Flagged: {reason}.",
    )
    messages.success(request, "Thanks! Your report was sent to the Face Value team.")
    return redirect("product_library:detail", pk=product.pk)
