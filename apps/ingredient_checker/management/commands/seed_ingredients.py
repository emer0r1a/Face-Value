from django.core.management.base import BaseCommand

from apps.ingredient_checker.models import IngredientInteraction
from apps.product_library.models import Ingredient

INGREDIENTS = [
    ("Retinol", "Vitamin A derivative; supports skin renewal",
     "Can cause dryness or irritation. Use sunscreen daily."),
    ("Glycolic Acid", "AHA exfoliant", "Can sting or increase sun sensitivity."),
    ("Salicylic Acid", "BHA exfoliant; works inside pores", "May dry out skin if overused."),
    ("Lactic Acid", "Gentle AHA exfoliant", "May increase sun sensitivity."),
    ("Benzoyl Peroxide", "Acne-fighting antibacterial", "Can bleach fabric and dry the skin."),
    ("Vitamin C", "Antioxidant; brightening", "Can tingle on sensitive skin."),
    ("Niacinamide", "Vitamin B3; supports the skin barrier", "Usually well tolerated."),
    ("Hyaluronic Acid", "Humectant; draws water into skin", "Usually well tolerated."),
    ("Ceramides", "Barrier-supporting lipids", ""),
    ("Glycerin", "Humectant", ""),
]

INTERACTIONS = [
    ("Retinol", "Glycolic Acid", "high",
     "Retinol and AHAs are both exfoliating. Layering them may cause redness, peeling, or stinging.",
     "Try them on alternate nights."),
    ("Retinol", "Salicylic Acid", "high",
     "Retinol and BHA together can be very drying for some skin.",
     "Use on separate nights, or morning BHA and evening retinol."),
    ("Retinol", "Benzoyl Peroxide", "high",
     "Benzoyl peroxide can make retinol less stable and irritating together.",
     "Apply at different times of day."),
    ("Retinol", "Vitamin C", "moderate",
     "Both are active ingredients and can irritate when layered.",
     "Vitamin C in the morning, retinol at night."),
    ("Glycolic Acid", "Vitamin C", "moderate",
     "Acids plus vitamin C may sting on sensitive skin.",
     "Space them apart or alternate days."),
    ("Glycolic Acid", "Salicylic Acid", "moderate",
     "Using two exfoliating acids at once can over-exfoliate.",
     "Pick one per routine."),
    ("Lactic Acid", "Retinol", "moderate",
     "Both exfoliate and may irritate when layered.",
     "Alternate nights."),
]


class Command(BaseCommand):
    help = "Seed common ingredients and well-known interactions (safe to re-run)."

    def handle(self, *args, **opts):
        by_name = {}
        for name, func, caution in INGREDIENTS:
            obj, _ = Ingredient.objects.get_or_create(
                ingredient_name=name,
                defaults={"function": func, "description": func, "caution": caution},
            )
            by_name[name] = obj

        made = 0
        for a, b, sev, msg, tip in INTERACTIONS:
            _, created = IngredientInteraction.objects.get_or_create(
                ingredient_1=by_name[a], ingredient_2=by_name[b],
                defaults={"severity": sev, "warning_message": msg, "recommendation": tip},
            )
            made += created
        self.stdout.write(self.style.SUCCESS(
            f"{len(by_name)} ingredients ready, {made} new interactions."))
