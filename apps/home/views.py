from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.ingredient_checker.models import IngredientAlert, IngredientInteraction
from apps.notifications.models import Notification
from apps.product_library import expiry
from apps.product_library.models import Product, ProductHistory, ProductIngredient
from apps.product_library.services import shopping_items
from apps.product_library.views import art_for
from apps.routine_builder.models import Routine
from apps.routine_builder.services import DAY_KEYS, DAY_NAMES, checks_for, is_scheduled_on, product_facts
from apps.routine_tracker.logic import streaks
from apps.routine_tracker.models import RoutineLog
from apps.routine_tracker.services import build_summary, required_weekdays

from . import vibe

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


def _streaks(user, dates, today):
    """(current, best). Shared with the tracker page so both always agree;
    days with nothing scheduled don't break a streak."""
    return streaks(dates, today, required_weekdays(user))


def _care_notes(products, active_routines, today):
    """Expiry and timing heads-ups for the dashboard (at most four)."""
    notes = []
    for p in products:
        ex = expiry.info(p.opened_on, p.pao_months, today)
        if p.status == "active" and ex and ex["state"] in ("expired", "soon"):
            notes.append({
                "icon": "⏳", "title": f"{p.product_name} {'has expired' if ex['state'] == 'expired' else 'expires soon'}",
                "text": ex["label"] + ".", "url": reverse("product_library:detail", args=[p.pk]), "level": ex["state"],
            })
    facts = product_facts({it.product_id for r in active_routines for it in r.items.all()}, today)
    for r in active_routines:
        for c in checks_for(r.routine_type.lower(), [it.product_id for it in r.items.all()], facts):
            if c["key"] in ("no-spf", "retinoid-day"):
                notes.append({
                    "icon": c["icon"], "title": c["title"], "text": f"{r.routine_name}. {c['tip']}",
                    "url": reverse("routine_builder:edit", args=[r.pk]), "level": "warn",
                })
    notes.sort(key=lambda n: n["level"] == "soon")  # expired and warnings first
    return notes[:4]


VIBE_LINKS = {
    "routines": "routine_builder:list", "add_product": "product_library:add",
    "shopping": "product_library:shopping", "ingredients": "ingredient_checker:hub",
    "tracker": "routine_tracker:tracker",
}


@login_required
def home_view(request):
    user = request.user
    today = timezone.localdate()

    dates = _completed_dates(user)
    streak, best = _streaks(user, dates, today)

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

    summary, _logs = build_summary(user, today, active_routines)
    vibe_data = vibe.build(user, today, active_routines, summary["week_pct"], streak, products)
    for tip in vibe_data["tips"]:
        tip["url"] = reverse(VIBE_LINKS[tip["link"]])

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
        "vibe": vibe_data,
        "care": _care_notes(products, active_routines, today),
        "shopping_count": shopping_items(user, today)["count"],
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

    streak, best = _streaks(request.user, _completed_dates(request.user), today)
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
