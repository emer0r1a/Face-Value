from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.ingredient_checker.models import IngredientAlert, IngredientInteraction
from apps.notifications.models import Notification
from apps.product_library.models import Product, ProductHistory, ProductIngredient
from apps.product_library.views import art_for
from apps.routine_builder.models import Routine
from apps.routine_builder.services import DAY_KEYS, DAY_NAMES, is_scheduled_on
from apps.routine_tracker.models import RoutineLog

DONE = "completed"

TIPS = [
    ("Patch test first", "Try a new product on your inner arm for a day before it goes anywhere near your face."),
    ("SPF is the last step", "Sunscreen goes on at the end of your morning routine, even on cloudy days."),
    ("One new thing at a time", "Add a single new active, then give it a couple of weeks before adding another."),
    ("Take turns", "Retinol and exfoliating acids can be a lot together. Alternating nights is a gentle approach."),
    ("Thin to thick", "Layer products from the lightest texture to the richest so each one can do its job."),
    ("Squeaky isn't the goal", "If your face feels tight after cleansing, try a gentler formula."),
]


def _completed_dates(user):
    return set(
        RoutineLog.objects.filter(user=user, status=DONE)
        .values_list("log_date", flat=True)
    )


def _streaks(dates, today):
    """Return (current, best) streak lengths from a set of dates."""
    if not dates:
        return 0, 0

    # current: walk back from today (or yesterday if today isn't done yet)
    day = today if today in dates else today - timedelta(days=1)
    current = 0
    while day in dates:
        current += 1
        day -= timedelta(days=1)

    best = run = 0
    prev = None
    for d in sorted(dates):
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return current, best


def _vibe(products, routines):
    """Balance/hydration/shelf cards, all derived from the user's own data."""
    cats = [(p.category or "").lower() for p in products]
    has = lambda *words: any(w in c for c in cats for w in words)

    types = {r.routine_type.lower() for r in routines}
    balance = 0
    balance += 40 if "morning" in types else 0
    balance += 40 if "evening" in types else 0
    balance += 20 if has("sunscreen", "spf") else 0

    hydration = 0
    hydration += 50 if has("moistur", "cream") else 0
    hydration += 30 if has("serum", "essence", "toner", "hydrat") else 0
    hydration += 20 if has("cleanser") else 0

    inactive = [p for p in products if p.status != "active"]
    shelf = 100 if products and not inactive else (0 if not products else 60)

    return [
        {"key": "balance", "label": "Routine balance", "value": balance,
         "hint": "Morning + evening + SPF" if balance < 100 else "Beautifully balanced"},
        {"key": "hydration", "label": "Hydration", "value": hydration,
         "hint": "Add a moisturizer or serum" if hydration < 80 else "Plenty of moisture"},
        {"key": "shelf", "label": "Shelf freshness", "value": shelf,
         "hint": (f"{len(inactive)} product(s) need a look" if inactive
                  else ("Add your first product" if not products else "All products active"))},
    ]


@login_required
def home_view(request):
    user = request.user
    today = timezone.localdate()

    dates = _completed_dates(user)
    streak, best = _streaks(dates, today)

    week = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        week.append({"label": d.strftime("%a")[0], "done": d in dates, "today": d == today})

    done_today = set(
        RoutineLog.objects.filter(user=user, log_date=today, status=DONE)
        .values_list("routine_id", flat=True)
    )
    # Only routines scheduled for today show up here. A routine with no
    # schedule rows at all counts as "every day".
    today_key = DAY_KEYS[today.weekday()]
    active_routines = list(
        Routine.objects.filter(user=user, status="active")
        .prefetch_related("items__product", "schedules")
        .order_by("routine_name")
    )
    routines = [r for r in active_routines if is_scheduled_on(r, today_key)]
    off_today = len(active_routines) - len(routines)
    done_today &= {r.id for r in routines}
    order = {"morning": 0, "afternoon": 1, "evening": 2}
    routines.sort(key=lambda r: (order.get(r.routine_type.lower(), 9), r.routine_name))
    for r in routines:
        r.done_today = r.id in done_today
        r.sched_time = next((s.scheduled_time for s in r.schedules.all() if s.is_active), None)
        r.step_list = list(r.items.all())
        for it in r.step_list:
            it.product.art = art_for(it.product.category)

    products = list(Product.objects.filter(user=user).order_by("product_name"))
    for p in products:
        p.art = art_for(p.category)
    shelf = sorted(
        [p for p in products if p.status == "active"],
        key=lambda p: p.date_added, reverse=True,
    )[:8]
    alerts = (
        IngredientAlert.objects.filter(user=user, is_read=False)
        .select_related("interaction__ingredient_1", "interaction__ingredient_2")
        .order_by("-created_at")[:3]
    )
    activity = (
        ProductHistory.objects.filter(user=user)
        .select_related("product").order_by("-action_date")[:5]
    )
    reminders = Notification.objects.filter(user=user, is_read=False).order_by("scheduled_at")[:3]

    return render(request, "home/home.html", {
        "streak": streak,
        "best_streak": best,
        "week": week,
        "routines": routines,
        "off_today": off_today,
        "today_name": DAY_NAMES[today_key],
        "routines_done": len(done_today),
        "routine_types": sorted({r.routine_type.lower() for r in routines}, key=lambda t: order.get(t, 9)),
        "shelf": shelf,
        "tips": TIPS,
        "caution_total": IngredientAlert.objects.filter(user=user, is_read=False).count(),
        "done_pct": round(100 * len(done_today) / len(routines)) if routines else 0,
        "products": products,
        "alerts": alerts,
        "activity": activity,
        "reminders": reminders,
        "vibe": _vibe(products, routines),
        "hour": timezone.localtime().hour,
    })


@login_required
@require_POST
def toggle_routine(request, routine_id):
    """Mark a routine done (or undo) for today. Returns the fresh streak."""
    routine = get_object_or_404(Routine, pk=routine_id, user=request.user)
    today = timezone.localdate()
    done = request.POST.get("done") == "1"

    log, _ = RoutineLog.objects.get_or_create(
        routine=routine, user=request.user, log_date=today,
        defaults={"status": "pending"},
    )
    log.status = DONE if done else "pending"
    log.completed_at = timezone.now() if done else None
    log.save()

    streak, best = _streaks(_completed_dates(request.user), today)
    return JsonResponse({"ok": True, "done": done, "streak": streak, "best": best})


@login_required
@require_GET
def clash_check(request):
    """Cross-reference the ingredients of two of the user's products."""
    ids = [request.GET.get("a"), request.GET.get("b")]
    if not all(i and i.isdigit() for i in ids) or ids[0] == ids[1]:
        return JsonResponse({"error": "Pick two different products."}, status=400)

    a = get_object_or_404(Product, pk=ids[0], user=request.user)
    b = get_object_or_404(Product, pk=ids[1], user=request.user)

    def ing_ids(p):
        return set(ProductIngredient.objects.filter(product=p).values_list("ingredient_id", flat=True))

    ia, ib = ing_ids(a), ing_ids(b)
    hits = IngredientInteraction.objects.filter(
        Q(ingredient_1__in=ia, ingredient_2__in=ib) | Q(ingredient_1__in=ib, ingredient_2__in=ia)
    ).select_related("ingredient_1", "ingredient_2")

    return JsonResponse({
        "products": [str(a), str(b)],
        "has_ingredients": bool(ia and ib),
        "clashes": [{
            "pair": f"{h.ingredient_1.ingredient_name} + {h.ingredient_2.ingredient_name}",
            "severity": h.severity.lower(),
            "message": h.warning_message,
            "tip": h.recommendation,
        } for h in hits],
    })
