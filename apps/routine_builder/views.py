from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.ingredient_checker.models import IngredientAlert
from apps.product_library.models import Product
from apps.product_library.views import art_for

from .models import Routine, RoutineItem, RoutineSchedule
from .services import (
    DAY_KEYS,
    DAY_NAMES,
    DAYS,
    MAX_STEPS,
    SLOT_EMOJI,
    SLOT_KEYS,
    SLOT_ORDER,
    SLOT_TONE,
    SLOTS,
    default_step_name,
    default_time,
    checks_for,
    find_clashes,
    product_facts,
    scheduled_days,
    sync_alerts,
)

NAME_MAX = 100
STEP_NAME_MAX = 50
DESCRIPTION_MAX = 500


def _own_routine(request, pk):
    return get_object_or_404(Routine, pk=pk, user=request.user)


def _routine_time(routine):
    for s in routine.schedules.all():
        return s.scheduled_time
    return default_time(routine.routine_type)


def _fmt_time(t):
    return t.strftime("%I:%M %p").lstrip("0")


# ---------------------------------------------------------------- list + planner

@login_required
def routine_list_view(request):
    user = request.user
    today_key = DAY_KEYS[timezone.localdate().weekday()]

    routines = list(
        Routine.objects.filter(user=user)
        .prefetch_related(
            Prefetch("items", queryset=RoutineItem.objects.select_related("product")),
            "schedules",
        )
    )
    routines.sort(key=lambda r: (SLOT_ORDER.get(r.routine_type.lower(), 9), r.routine_name.lower()))

    clash_counts = dict(
        IngredientAlert.objects.filter(user=user)
        .values("routine_id").annotate(n=Count("id")).values_list("routine_id", "n")
    )

    today = timezone.localdate()
    facts = product_facts([it.product_id for r in routines for it in r.items.all()], today)

    payload = []
    for r in routines:
        slot = r.routine_type.lower()
        days = scheduled_days(r)
        r.checks = [c for c in checks_for(slot, [it.product_id for it in r.items.all()], facts) if c["severity"] == "warn"]
        r.slot = slot
        r.tone = SLOT_TONE.get(slot, "lime")
        r.emoji = SLOT_EMOJI.get(slot, "🌿")
        r.is_active = r.status == "active"
        r.time_label = _fmt_time(_routine_time(r))
        r.clash_count = clash_counts.get(r.pk, 0)
        r.step_list = list(r.items.all())
        for it in r.step_list:
            it.product.art = art_for(it.product.category)
        r.preview_steps = r.step_list[:4]
        r.more_steps = max(0, len(r.step_list) - 4)
        r.day_dots = [
            {"key": k, "letter": short[0], "full": full, "on": k in days}
            for k, short, full in DAYS
        ]
        payload.append({
            "id": r.pk, "name": r.routine_name, "type": slot,
            "paused": not r.is_active, "days": sorted(days, key=DAY_KEYS.index),
        })

    # planner[slot][day] -> routines
    cells = {(s[0], d[0]): [] for s in SLOTS for d in DAYS}
    for r in routines:
        for k in scheduled_days(r):
            if (r.slot, k) in cells:
                cells[(r.slot, k)].append(r)

    planner = [{
        "key": key, "label": label, "emoji": emoji, "tone": tone,
        "cells": [
            {"day": dk, "full": full, "today": dk == today_key, "routines": cells[(key, dk)]}
            for dk, _short, full in DAYS
        ],
    } for key, label, emoji, tone in SLOTS]

    weekly_sessions = sum(len(scheduled_days(r)) for r in routines if r.is_active)

    return render(request, "routine_builder/routine_list.html", {
        "routines": routines,
        "routines_json": payload,
        "planner": planner,
        "days": [{"key": k, "short": s, "full": f, "today": k == today_key} for k, s, f in DAYS],
        "slots": [{"key": k, "label": l, "emoji": e, "tone": t} for k, l, e, t in SLOTS],
        "today_name": DAY_NAMES[today_key],
        "active_count": sum(1 for r in routines if r.is_active),
        "weekly_sessions": weekly_sessions,
        "product_count": Product.objects.filter(user=user, status="active").count(),
    })


@login_required
@require_POST
def schedule_toggle_view(request, pk):
    """Planner click-to-schedule: put a routine on (or take it off) one day."""
    routine = _own_routine(request, pk)
    day = request.POST.get("day", "")
    if day not in DAY_KEYS:
        return JsonResponse({"ok": False, "error": "Unknown day."}, status=400)
    on = request.POST.get("on") == "1"

    existing = list(routine.schedules.all())
    when = existing[0].scheduled_time if existing else default_time(routine.routine_type)

    if on:
        row, created = RoutineSchedule.objects.get_or_create(
            routine=routine, day_of_week=day,
            defaults={"scheduled_time": when, "is_active": True},
        )
        if not created and not row.is_active:
            row.is_active = True
            row.save(update_fields=["is_active"])
    else:
        routine.schedules.filter(day_of_week=day).delete()

    days = sorted(
        RoutineSchedule.objects.filter(routine=routine, is_active=True)
        .values_list("day_of_week", flat=True),
        key=lambda d: DAY_KEYS.index(d) if d in DAY_KEYS else 99,
    )
    return JsonResponse({"ok": True, "days": days})


@login_required
@require_POST
def routine_status_view(request, pk):
    routine = _own_routine(request, pk)
    pausing = routine.status == "active"
    routine.status = "paused" if pausing else "active"
    routine.save(update_fields=["status"])
    messages.success(
        request,
        f"“{routine.routine_name}” is paused. It won't show on your dashboard."
        if pausing else f"“{routine.routine_name}” is back on your dashboard.",
    )
    return redirect("routine_builder:list")


@login_required
@require_POST
def routine_delete_view(request, pk):
    routine = _own_routine(request, pk)
    name = routine.routine_name
    routine.delete()
    messages.success(request, f"“{name}” was removed.")
    return redirect("routine_builder:list")


@login_required
@require_GET
def clash_preview_view(request):
    """Live clash check for the builder: ?ids=1,2,3 (the steps, in order)."""
    ids = [int(i) for i in request.GET.get("ids", "").split(",") if i.strip().isdigit()]
    ids = ids[:MAX_STEPS]
    slot = request.GET.get("type", "").lower()
    owned = set(Product.objects.filter(user=request.user, pk__in=ids).values_list("pk", flat=True))
    kept = [i for i in ids if i in owned]
    checks = checks_for(slot, kept, product_facts(kept, timezone.localdate()))
    clashes = find_clashes(request.user, [i for i in ids if i in owned])
    have_ingredients = (
        Product.objects.filter(user=request.user, pk__in=owned, product_ingredients__isnull=False)
        .distinct().count()
    )
    return JsonResponse({
        "checked": len(owned),
        "with_ingredients": have_ingredients,
        "checks": checks,
        "clashes": [{
            "pair": c["pair"], "products": c["products"], "severity": c["severity"],
            "message": c["message"], "tip": c["tip"],
        } for c in clashes],
    })


# ---------------------------------------------------------------- builder form

def _product_payload(p):
    return {
        "id": p.pk,
        "name": p.product_name,
        "brand": p.brand,
        "category": p.category,
        "art": art_for(p.category),
        "image": p.image.url if p.image else "",
        "archived": p.status != "active",
        "step": default_step_name(p.category),
    }


def _parse_time(raw, fallback):
    try:
        return datetime.strptime((raw or "").strip()[:5], "%H:%M").time()
    except ValueError:
        return fallback


def _routine_form(request, routine=None):
    user = request.user
    editing = routine is not None

    if request.method == "POST":
        name = request.POST.get("routine_name", "").strip()
        description = request.POST.get("description", "").strip()
        slot = request.POST.get("routine_type", "").strip().lower()
        picked = set(request.POST.getlist("days"))
        days = [k for k in DAY_KEYS if k in picked]
        time_ok = bool(request.POST.get("time", "").strip())
        when = _parse_time(request.POST.get("time"), default_time(slot))
        raw_ids = request.POST.getlist("step_product")
        raw_names = request.POST.getlist("step_name")

        wanted = []
        for i, raw in enumerate(raw_ids):
            if raw.isdigit() and int(raw) not in [w[0] for w in wanted]:
                label = raw_names[i].strip() if i < len(raw_names) else ""
                wanted.append((int(raw), label))
        owned = {p.pk: p for p in Product.objects.filter(user=user, pk__in=[w[0] for w in wanted])}
        steps = [(owned[pid], label) for pid, label in wanted if pid in owned]

        error = None
        if not name:
            error = "Give your routine a name."
        elif len(name) > NAME_MAX:
            error = f"The name must be {NAME_MAX} characters or fewer."
        elif slot not in SLOT_KEYS:
            error = "Choose morning, afternoon or evening."
        elif len(description) > DESCRIPTION_MAX:
            error = f"The note must be {DESCRIPTION_MAX} characters or fewer."
        elif not days:
            error = "Pick at least one day."
        elif not time_ok:
            error = "Choose a time for your reminder."
        elif not steps:
            error = "Add at least one product to your routine."
        elif len(steps) > MAX_STEPS:
            error = f"A routine can have up to {MAX_STEPS} steps."
        elif any(len(label) > STEP_NAME_MAX for _p, label in steps):
            error = f"Step names must be {STEP_NAME_MAX} characters or fewer."
        elif (
            Routine.objects.filter(user=user, routine_name__iexact=name)
            .exclude(pk=routine.pk if editing else None).exists()
        ):
            error = "You already have a routine with that name."

        if not error:
            with transaction.atomic():
                if not editing:
                    routine = Routine(user=user)
                routine.routine_name = name
                routine.routine_type = slot
                routine.description = description
                routine.save()

                routine.items.all().delete()
                RoutineItem.objects.bulk_create([
                    RoutineItem(
                        routine=routine, product=p, step_number=n,
                        step_name=label or default_step_name(p.category),
                    )
                    for n, (p, label) in enumerate(steps, start=1)
                ])
                routine.schedules.all().delete()
                RoutineSchedule.objects.bulk_create([
                    RoutineSchedule(routine=routine, day_of_week=d, scheduled_time=when, is_active=True)
                    for d in days
                ])
                clash_total = sync_alerts(routine)

            messages.success(
                request,
                f"“{routine.routine_name}” {'updated' if editing else 'created'}. "
                "It will show on your dashboard on the days you picked.",
            )
            if clash_total:
                messages.warning(
                    request,
                    f"Heads up: {clash_total} possible ingredient clash"
                    f"{'es' if clash_total != 1 else ''} in this routine. See your dashboard for tips.",
                )
            return redirect("routine_builder:list")

        initial = {
            "name": name, "description": description,
            "type": slot if slot in SLOT_KEYS else "morning",
            "days": days, "time": when.strftime("%H:%M"),
            "steps": [{"product": p.pk, "name": label} for p, label in steps],
        }
        in_routine = {p.pk for p, _ in steps}
    else:
        if editing:
            existing = list(routine.items.select_related("product"))
            initial = {
                "name": routine.routine_name,
                "description": routine.description,
                "type": routine.routine_type.lower() if routine.routine_type.lower() in SLOT_KEYS else "morning",
                "days": sorted(scheduled_days(routine), key=DAY_KEYS.index),
                "time": _routine_time(routine).strftime("%H:%M"),
                "steps": [{"product": it.product_id, "name": it.step_name} for it in existing],
            }
            in_routine = {it.product_id for it in existing}
        else:
            slot = request.GET.get("type", "").lower()
            slot = slot if slot in SLOT_KEYS else "morning"
            day = request.GET.get("day", "")
            initial = {
                "name": "", "description": "", "type": slot,
                "days": [day] if day in DAY_KEYS else list(DAY_KEYS),
                "time": default_time(slot).strftime("%H:%M"),
                "steps": [],
            }
            in_routine = set()
        error = None

    products = [
        p for p in Product.objects.filter(user=user).order_by("product_name")
        if p.status == "active" or p.pk in in_routine
    ]

    return render(request, "routine_builder/routine_form.html", {
        "routine": routine if editing else None,
        "error": error,
        "initial": initial,
        "products_json": [_product_payload(p) for p in products],
        "product_count": len(products),
        "slots": [{"key": k, "label": l, "emoji": e, "tone": t} for k, l, e, t in SLOTS],
        "days": [{"key": k, "short": s, "full": f} for k, s, f in DAYS],
        "max_steps": MAX_STEPS,
        "name_max": NAME_MAX,
    })


@login_required
def routine_create_view(request):
    return _routine_form(request)


@login_required
def routine_edit_view(request, pk):
    return _routine_form(request, _own_routine(request, pk))
