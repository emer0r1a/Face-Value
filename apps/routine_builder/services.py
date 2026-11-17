"""Shared helpers for the routine builder and the dashboard.

Routine.routine_type holds the slot ("morning" / "afternoon" / "evening") and
RoutineSchedule.day_of_week holds a short lowercase day key ("mon" ... "sun"),
so no model changes were needed.
"""
from collections import defaultdict
from datetime import time
from itertools import combinations

from django.db.models import Q

from apps.ingredient_checker.models import IngredientAlert, IngredientInteraction
from apps.product_library.models import ProductIngredient

# (key, short label, full name)
DAYS = [
    ("mon", "Mon", "Monday"),
    ("tue", "Tue", "Tuesday"),
    ("wed", "Wed", "Wednesday"),
    ("thu", "Thu", "Thursday"),
    ("fri", "Fri", "Friday"),
    ("sat", "Sat", "Saturday"),
    ("sun", "Sun", "Sunday"),
]
DAY_KEYS = [d[0] for d in DAYS]
DAY_NAMES = {d[0]: d[2] for d in DAYS}

# (key, label, emoji, tone class used by the theme)
SLOTS = [
    ("morning", "Morning", "☀️", "sun"),
    ("afternoon", "Afternoon", "🌤️", "sky"),
    ("evening", "Evening", "🌙", "lav"),
]
SLOT_KEYS = [s[0] for s in SLOTS]
SLOT_ORDER = {k: i for i, k in enumerate(SLOT_KEYS)}
SLOT_TONE = {s[0]: s[3] for s in SLOTS}
SLOT_EMOJI = {s[0]: s[2] for s in SLOTS}

DEFAULT_TIMES = {
    "morning": time(7, 0),
    "afternoon": time(13, 0),
    "evening": time(20, 0),
}

MAX_STEPS = 12

STEP_VERBS = {
    "cleanser": "Cleanse",
    "toner": "Tone",
    "serum": "Treat",
    "moisturizer": "Moisturize",
    "sunscreen": "Protect",
    "exfoliant": "Exfoliate",
    "mask": "Mask",
    "eye care": "Eye care",
    "treatment": "Treat",
}

_SEVERITY_ORDER = {"high": 0, "moderate": 1, "medium": 1, "low": 2}


def default_step_name(category):
    return STEP_VERBS.get((category or "").lower(), "Apply")


def default_time(routine_type):
    return DEFAULT_TIMES.get((routine_type or "").lower(), time(8, 0))


def scheduled_days(routine):
    """Set of day keys this routine is active on (uses prefetched schedules)."""
    return {s.day_of_week for s in routine.schedules.all() if s.is_active}


def is_scheduled_on(routine, day_key):
    """A routine with no schedule rows at all counts as 'every day', so
    routines created before the scheduler existed keep showing up."""
    rows = list(routine.schedules.all())
    if not rows:
        return True
    return any(s.is_active and s.day_of_week == day_key for s in rows)


def find_clashes(user, product_ids):
    """Known ingredient interactions between any two of the user's products.

    Returns a list of dicts sorted by severity, one per (product pair,
    interaction). Only products owned by ``user`` are considered.
    """
    ordered = []
    for pid in product_ids:
        if pid not in ordered:
            ordered.append(pid)
    if len(ordered) < 2:
        return []

    ingredients = defaultdict(set)
    names = {}
    rows = (
        ProductIngredient.objects
        .filter(product__user=user, product_id__in=ordered)
        .values_list("product_id", "ingredient_id", "product__product_name")
    )
    for product_id, ingredient_id, product_name in rows:
        ingredients[product_id].add(ingredient_id)
        names[product_id] = product_name

    all_ids = set().union(*ingredients.values()) if ingredients else set()
    if not all_ids:
        return []

    interactions = list(
        IngredientInteraction.objects
        .filter(Q(ingredient_1__in=all_ids) | Q(ingredient_2__in=all_ids))
        .select_related("ingredient_1", "ingredient_2")
    )

    found = []
    for a, b in combinations([p for p in ordered if p in names], 2):
        ia, ib = ingredients[a], ingredients[b]
        for it in interactions:
            i1, i2 = it.ingredient_1_id, it.ingredient_2_id
            if (i1 in ia and i2 in ib) or (i1 in ib and i2 in ia):
                found.append({
                    "interaction_id": it.pk,
                    "products": [names[a], names[b]],
                    "pair": f"{it.ingredient_1.ingredient_name} + {it.ingredient_2.ingredient_name}",
                    "severity": it.severity.lower(),
                    "message": it.warning_message,
                    "tip": it.recommendation,
                })
    found.sort(key=lambda c: _SEVERITY_ORDER.get(c["severity"], 3))
    return found


def sync_alerts(routine):
    """Keep the routine's IngredientAlert rows in step with its products.

    Alerts that still apply are left alone (so "read" state survives edits),
    new clashes get an alert, and alerts for clashes that are gone are removed.
    Returns the number of clashes now flagged.
    """
    product_ids = list(routine.items.values_list("product_id", flat=True))
    clashes = find_clashes(routine.user, product_ids)

    wanted = {}
    for c in clashes:
        wanted.setdefault(c["interaction_id"], c)

    existing = {a.interaction_id: a for a in routine.ingredient_alerts.all()}
    stale = [a.pk for iid, a in existing.items() if iid not in wanted]
    if stale:
        IngredientAlert.objects.filter(pk__in=stale).delete()

    for iid, c in wanted.items():
        if iid in existing:
            continue
        IngredientAlert.objects.create(
            user=routine.user,
            routine=routine,
            interaction_id=iid,
            severity=c["severity"],
            alert_message=(
                f"{c['products'][0]} and {c['products'][1]} are both in your "
                f"{routine.routine_name} routine. {c['message']}"
                + (f" {c['tip']}" if c["tip"] else "")
            ),
        )
    return len(wanted)
