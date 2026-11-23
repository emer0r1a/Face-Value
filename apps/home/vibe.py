"""The Skin Vibe Meter: five friendly scores and one overall "vibe".

``compute`` is pure (plain numbers in, dict out) so it is easy to test;
``build`` gathers the numbers from the database. Nothing here is medical
advice, it only looks at the routines and products the user has saved.
"""
from apps.ingredient_checker.models import IngredientAlert
from apps.ingredient_checker.services import group_for
from apps.product_library import expiry
from apps.product_library.models import ProductIngredient
from apps.routine_builder.services import checks_for, product_facts

ROLES = {
    "cleanse": ("cleanser",),
    "treat": ("toner", "serum", "treatment", "exfoliant", "mask", "eye care"),
    "moisturize": ("moisturizer",),
    "protect": ("sunscreen",),
}
ROLE_LABEL = {"cleanse": "a cleanser", "treat": "a treatment step (serum, toner or treatment)",
              "moisturize": "a moisturizer", "protect": "a sunscreen in a morning routine"}
WEIGHTS = {"balance": 25, "hydration": 15, "harmony": 25, "freshness": 15, "consistency": 20}
HYDRATING_GROUPS = {"hydrators", "barrier"}

LEVELS = [(85, "Glowing", "🌸"), (65, "Balanced", "🌿"), (40, "Getting there", "🌱"), (0, "Needs a little love", "🌧️")]


def _clamp(n):
    return max(0, min(100, round(n)))


def compute(*, roles, hydrators, ingredient_data, clashes, day_warns, fresh, week_pct, streak,
            has_routines, has_products):
    """Return {"score", "level", "emoji", "cards", "tips"}.

    roles: set of ROLES keys covered by active routines
    hydrators: number of distinct hydrating/barrier ingredients in them
    ingredient_data: do those products have any saved ingredients?
    clashes: {"high": n, "moderate": n, "low": n} on active routines
    day_warns: sanity-check warnings (no SPF by day, retinoid by day)
    fresh: {"tracked": n, "expired": n, "soon": n} or None
    """
    cards, tips = [], []

    # Balance
    if has_routines:
        balance = 25 * len(roles)
        missing = [r for r in ROLES if r not in roles]
        hint = "All four steps covered" if not missing else f"Missing {ROLE_LABEL[missing[0]].split(' (')[0]}"
    else:
        balance, missing, hint = 0, list(ROLES), "Build a routine to start"
    cards.append({"key": "balance", "label": "Routine balance", "value": balance, "hint": hint, "tone": "lime", "emoji": "⚖️"})
    if has_routines and missing:
        tips.append({"weight": 100 - balance, "text": f"Add {ROLE_LABEL[missing[0]]} to your routines.",
                     "link": "add_product" if missing[0] != "protect" else "shopping"})
    elif not has_routines:
        tips.append({"weight": 100, "text": "Build your first routine to unlock your vibe.", "link": "routines"})

    # Hydration
    if not has_routines:
        hydration, hint = 0, "No routine yet"
    elif ingredient_data:
        hydration = _clamp(hydrators * 25)
        hint = "Plenty of moisture" if hydration >= 75 else "Add a humectant like hyaluronic acid"
    else:
        hydration = 70 if "moisturize" in roles else 25
        hint = "Add ingredient lists for a precise score"
    cards.append({"key": "hydration", "label": "Hydration", "value": hydration, "hint": hint, "tone": "sky", "emoji": "💧"})
    if has_routines and hydration < 60:
        tips.append({"weight": 100 - hydration, "text": "Boost hydration with a humectant or barrier ingredient.", "link": "ingredients"})

    # Harmony: clashes + sanity-check warnings
    penalty = 30 * clashes.get("high", 0) + 15 * clashes.get("moderate", 0) + 5 * clashes.get("low", 0) + 10 * day_warns
    harmony = _clamp(100 - penalty) if has_routines else 0
    n_clash = sum(clashes.values())
    if not has_routines:
        hint = "No routine yet"
    elif n_clash or day_warns:
        bits = ([f"{n_clash} clash{'es' if n_clash != 1 else ''}"] if n_clash else []) + ([f"{day_warns} timing tip{'s' if day_warns != 1 else ''}"] if day_warns else [])
        hint = " and ".join(bits) + " to look at"
    else:
        hint = "No clashes found"
    cards.append({"key": "harmony", "label": "Harmony", "value": harmony, "hint": hint, "tone": "pink", "emoji": "🤝"})
    if has_routines and harmony < 100:
        tips.append({"weight": 100 - harmony, "text": "Sort out the clashes and timing tips in your routines.", "link": "routines"})

    # Freshness
    if fresh and fresh["tracked"]:
        freshness = _clamp(100 - 35 * fresh["expired"] - 12 * fresh["soon"])
        if fresh["expired"]:
            hint = f"{fresh['expired']} expired or finished"
        elif fresh["soon"]:
            hint = f"{fresh['soon']} expiring soon"
        else:
            hint = "Everything is fresh"
        if freshness < 100:
            tips.append({"weight": 100 - freshness, "text": "Replace what has expired or run out.", "link": "shopping"})
    else:
        freshness = None
        hint = "Add open dates to track" if has_products else "Add your first product"
    cards.append({"key": "freshness", "label": "Freshness", "value": freshness, "hint": hint, "tone": "sun", "emoji": "⏳"})

    # Consistency
    if has_routines:
        consistency = _clamp(0.7 * week_pct + 30 * min(streak, 7) / 7)
        hint = f"{streak}-day streak" if streak else "Check in today to start a streak"
    else:
        consistency, hint = 0, "Nothing to check in yet"
    cards.append({"key": "consistency", "label": "Consistency", "value": consistency, "hint": hint, "tone": "lav", "emoji": "🔥"})
    if has_routines and consistency < 60:
        tips.append({"weight": 100 - consistency, "text": "Check in your routines to grow your streak.", "link": "tracker"})

    have = [c for c in cards if c["value"] is not None]
    total_w = sum(WEIGHTS[c["key"]] for c in have)
    score = _clamp(sum(c["value"] * WEIGHTS[c["key"]] for c in have) / total_w) if (total_w and has_routines) else 0
    level, emoji = next((l, e) for floor, l, e in LEVELS if score >= floor)
    if not has_routines and not has_products:
        level, emoji = "Fresh start", "🌱"

    tips.sort(key=lambda t: -t["weight"])
    return {"score": score, "level": level, "emoji": emoji, "cards": cards, "tips": tips[:3]}


def build(user, today, active_routines, week_pct, streak, products):
    """Gather the numbers for ``compute`` from the user's saved data."""
    product_ids = {it.product_id for r in active_routines for it in r.items.all()}
    facts = product_facts(product_ids, today)

    roles = set()
    for r in active_routines:
        slot = r.routine_type.lower()
        for it in r.items.all():
            cat = (facts.get(it.product_id, {}).get("category") or "").lower()
            for role, words in ROLES.items():
                if cat in words and (role != "protect" or slot in ("morning", "afternoon")):
                    roles.add(role)

    hydrating, has_data = set(), False
    for ingredient_id, function in ProductIngredient.objects.filter(product_id__in=product_ids).values_list(
        "ingredient_id", "ingredient__function"
    ):
        has_data = True
        if group_for(function) in HYDRATING_GROUPS:
            hydrating.add(ingredient_id)

    clashes = {"high": 0, "moderate": 0, "low": 0}
    for sev in IngredientAlert.objects.filter(user=user, routine__status="active").values_list("severity", flat=True):
        sev = sev.lower()
        clashes["moderate" if sev == "medium" else sev if sev in clashes else "low"] += 1

    day_warns = 0
    for r in active_routines:
        ids = [it.product_id for it in r.items.all()]
        day_warns += sum(
            1 for c in checks_for(r.routine_type.lower(), ids, facts) if c["key"] in ("no-spf", "retinoid-day")
        )

    # Freshness covers every active product with a clock, plus finished ones in a routine
    tracked = expired = soon = 0
    for p in products:
        ex = expiry.info(p.opened_on, p.pao_months, today)
        if p.status == "finished" and p.pk in product_ids:
            tracked += 1
            expired += 1
        elif p.status == "active" and ex:
            tracked += 1
            expired += ex["state"] == "expired"
            soon += ex["state"] == "soon"

    return compute(
        roles=roles, hydrators=len(hydrating), ingredient_data=has_data, clashes=clashes,
        day_warns=day_warns, fresh={"tracked": tracked, "expired": expired, "soon": soon},
        week_pct=week_pct, streak=streak,
        has_routines=bool(active_routines), has_products=bool(products),
    )
