from django.core.management.base import BaseCommand

from apps.ingredient_checker.models import IngredientInteraction
from apps.product_library.models import Ingredient

# (name, function, description, caution)
# The function text decides which guide group the ingredient lands in
# (see apps/ingredient_checker/services.py), so keep its key words.
INGREDIENTS = [
    ("Retinol", "Vitamin A derivative; supports skin renewal",
     "A gentle form of vitamin A that speeds up cell turnover. Over time it can smooth texture, fade dark marks and help with breakouts.",
     "Can cause dryness or irritation while skin adjusts. Start slowly, use at night and wear sunscreen daily."),
    ("Bakuchiol", "Plant-based retinol alternative",
     "A plant-derived ingredient often used by people who find retinol too harsh. It supports smoother-looking skin.",
     "Usually gentle, but patch test first."),
    ("Glycolic Acid", "AHA exfoliant",
     "The smallest AHA, so it works fast on the skin's surface. It dissolves dull, dead cells for a smoother, brighter look.",
     "Can sting and increase sun sensitivity. Wear sunscreen."),
    ("Lactic Acid", "Gentle AHA exfoliant",
     "A milder AHA that also helps skin hold water. A good first step into chemical exfoliation.",
     "May increase sun sensitivity."),
    ("Mandelic Acid", "Gentle AHA exfoliant for sensitive skin",
     "A larger, slower AHA molecule, so it tends to be kinder to sensitive or easily flushed skin.",
     "May increase sun sensitivity."),
    ("Salicylic Acid", "BHA exfoliant; works inside pores",
     "Oil-soluble, so it can get into pores to loosen clogs. Popular for blackheads and oily or bumpy skin.",
     "May dry out skin if overused."),
    ("Benzoyl Peroxide", "Acne-fighting antibacterial",
     "Reduces the bacteria linked to breakouts and helps clear pores.",
     "Can bleach fabric and dry or irritate the skin."),
    ("Azelaic Acid", "Evens tone; clears blemishes",
     "Calms redness, fades marks left by breakouts and helps keep pores clear. Often well tolerated.",
     "May tingle at first."),
    ("Vitamin C", "Antioxidant; brightening",
     "Helps protect skin from daily environmental stress and brightens the look of dull or uneven skin.",
     "Can tingle on sensitive skin."),
    ("Ferulic Acid", "Antioxidant; stabilizes vitamin C",
     "A plant antioxidant often paired with vitamin C to help it last and work better.",
     ""),
    ("Niacinamide", "Vitamin B3; supports the skin barrier",
     "A versatile ingredient that supports the barrier, softens the look of pores and helps even out tone.",
     "Usually well tolerated."),
    ("Alpha Arbutin", "Brightening; fades dark spots",
     "Gently slows the pigment that causes dark spots, for a more even-looking tone.",
     ""),
    ("Tranexamic Acid", "Brightening; fades dark spots",
     "Helps with stubborn pigmentation and marks, and pairs well with other brighteners.",
     ""),
    ("Kojic Acid", "Brightening; fades dark spots",
     "Derived from fungi during fermentation; used to fade dark spots and uneven tone.",
     "Can irritate sensitive skin."),
    ("Hyaluronic Acid", "Humectant; draws water into skin",
     "Holds many times its weight in water, plumping the surface and leaving skin feeling hydrated.",
     "Usually well tolerated. Apply on damp skin and seal with a moisturizer."),
    ("Glycerin", "Humectant",
     "A classic, reliable moisturizer ingredient that pulls water into the top layer of skin.",
     ""),
    ("Panthenol", "Humectant; soothes and softens",
     "Vitamin B5. Helps skin hold on to moisture and feels calming on dry or irritated skin.",
     ""),
    ("Urea", "Humectant; softens rough skin",
     "Hydrates and, at higher strengths, gently smooths rough, dry patches.",
     "Higher strengths can sting on broken skin."),
    ("Ceramides", "Barrier-supporting lipids",
     "Fats that naturally sit between skin cells. Replacing them helps keep moisture in and irritants out.",
     ""),
    ("Squalane", "Lightweight emollient",
     "A weightless oil that softens skin without a greasy feel, and suits most skin types.",
     ""),
    ("Peptides", "Signal ingredients that support firmness",
     "Short chains of amino acids that tell skin to behave more youthfully, supporting a firmer, smoother look.",
     ""),
    ("Centella Asiatica", "Soothing; calms redness",
     "A calming plant extract often found in products for sensitive or stressed skin.",
     ""),
    ("Zinc Oxide", "Mineral sun filter; gentle on sensitive skin",
     "A mineral UV filter that sits on top of the skin. Often chosen for sensitive skin.",
     "Can leave a white cast on deeper skin tones."),
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
    ("Mandelic Acid", "Retinol", "moderate",
     "Both exfoliate and can irritate when layered.",
     "Alternate nights."),
    ("Benzoyl Peroxide", "Vitamin C", "moderate",
     "Benzoyl peroxide can break down vitamin C, which may make it less effective.",
     "Vitamin C in the morning, benzoyl peroxide at night."),
    ("Benzoyl Peroxide", "Glycolic Acid", "moderate",
     "A drying acne treatment plus an exfoliating acid may irritate.",
     "Use them at different times of day."),
    ("Benzoyl Peroxide", "Salicylic Acid", "low",
     "Both target breakouts, and together they can be drying for some skin.",
     "Start with one and add the other slowly."),
    ("Glycolic Acid", "Lactic Acid", "moderate",
     "Two AHAs at once can over-exfoliate.",
     "Pick one AHA per routine."),
    ("Salicylic Acid", "Lactic Acid", "moderate",
     "Combining a BHA and an AHA can be too much for some skin.",
     "Alternate days."),
]


class Command(BaseCommand):
    help = "Seed common ingredients and well-known interactions (safe to re-run)."

    def handle(self, *args, **opts):
        by_name = {}
        refreshed = 0
        for name, func, description, caution in INGREDIENTS:
            obj, created = Ingredient.objects.get_or_create(
                ingredient_name=name,
                defaults={"function": func, "description": description, "caution": caution},
            )
            # Fill in rows made by older seeds or by the "not yet classified"
            # placeholder, but never overwrite text an admin has written.
            placeholder = (
                obj.function.lower() == "not yet classified"
                or obj.description in ("", "No description available yet.", obj.function)
            )
            if not created and placeholder:
                obj.function, obj.description = func, description
                if not obj.caution:
                    obj.caution = caution
                obj.save()
                refreshed += 1
            by_name[name] = obj

        made = 0
        for a, b, sev, msg, tip in INTERACTIONS:
            _, created = IngredientInteraction.objects.get_or_create(
                ingredient_1=by_name[a], ingredient_2=by_name[b],
                defaults={"severity": sev, "warning_message": msg, "recommendation": tip},
            )
            made += created
        self.stdout.write(self.style.SUCCESS(
            f"{len(by_name)} ingredients ready ({refreshed} filled in), {made} new interactions."))
