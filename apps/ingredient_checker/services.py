"""Helpers for the Ingredient Checker & Guide Hub.

Ingredient.function is free text, so the guide groups ingredients by
keyword instead of needing a new model field.
"""

UNCLASSIFIED = "Not yet classified"

# (key, label, tone, keywords). The first group whose keyword appears in the
# lower-cased function text wins, so order matters.
GROUPS = [
    ("retinoids", "Retinoids", "lav", ("vitamin a", "retinol", "retinoid")),
    ("hydrators", "Hydrators", "sky", ("humectant", "hydrat", "draws water")),
    ("exfoliants", "Exfoliants", "pink", ("exfoliant", " aha", " bha", "peel")),
    ("antioxidants", "Antioxidants", "sun", ("antioxidant",)),
    ("sun", "Sun protection", "sun", ("sunscreen", "sun filter", "uv")),
    ("barrier", "Barrier & repair", "lime", ("barrier", "lipid", "emollient", "soothing", "firm", "repair")),
    ("blemish", "Blemish & tone", "pink", ("acne", "antibacterial", "blemish", "brighten", "dark spot", "tone")),
]
OTHER = ("other", "Not classified yet", "lime")


def is_classified(ingredient):
    return bool(ingredient.function) and ingredient.function.strip().lower() != UNCLASSIFIED.lower()


def group_for(function):
    text = f" {(function or '').lower()}"
    if not text.strip() or UNCLASSIFIED.lower() in text:
        return OTHER[0]
    for key, _label, _tone, words in GROUPS:
        if any(w in text for w in words):
            return key
    return OTHER[0]


def group_payload():
    groups = [{"key": k, "label": l, "tone": t} for k, l, t, _w in GROUPS]
    groups.append({"key": OTHER[0], "label": OTHER[1], "tone": OTHER[2]})
    return groups
