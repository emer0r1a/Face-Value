"""Database side of the tracker: loads a user's routines and check-ins into
plain data, then lets logic.py do the maths."""
from datetime import timedelta

from django.db.models import Prefetch

from apps.product_library.views import art_for
from apps.routine_builder.models import Routine, RoutineItem
from apps.routine_builder.services import scheduled_days

from . import logic
from .models import RoutineLog

DONE = "completed"
WINDOW = 7          # how many days back (including today) can be edited
HISTORY_DAYS = 200  # how much check-in history the page loads for the calendar


def active_routines(user):
    return list(
        Routine.objects.filter(user=user, status="active")
        .prefetch_related(
            Prefetch("items", queryset=RoutineItem.objects.select_related("product")),
            "schedules",
        )
        .order_by("routine_name")
    )


def plain_routines(routines):
    """Routines as the plain dicts logic.py expects (empty days = every day)."""
    return [{
        "id": r.pk,
        "days": scheduled_days(r),
        "created": r.created_at.date(),
    } for r in routines]


def required_weekdays(user):
    """Weekdays (Mon=0) the user has something scheduled, or None for 'every day'."""
    return logic.required_weekdays(plain_routines(active_routines(user)))


def load_history(user, today):
    """(logs, all_dates, total): recent {date: [ids]}, every check-in date, count."""
    pairs = set(
        RoutineLog.objects.filter(user=user, status=DONE)
        .values_list("log_date", "routine_id")
    )
    since = today - timedelta(days=HISTORY_DAYS)
    logs = {}
    for day, rid in pairs:
        if day >= since:
            logs.setdefault(day, []).append(rid)
    return logs, {d for d, _ in pairs}, len(pairs)


def build_summary(user, today, routines=None):
    routines = plain_routines(routines if routines is not None else active_routines(user))
    logs, dates, total = load_history(user, today)
    return logic.summary(routines, logs, today, dates=dates, total=total), logs


def routine_payload(r):
    """One routine for the page: schedule plus its steps."""
    sched = [s for s in r.schedules.all() if s.is_active]
    steps = []
    for it in r.items.all():
        steps.append({
            "name": it.step_name,
            "product": it.product.product_name,
            "art": art_for(it.product.category),
            "image": it.product.image.url if it.product.image else "",
        })
    return {
        "id": r.pk,
        "name": r.routine_name,
        "type": r.routine_type.lower(),
        "time": sched[0].scheduled_time.strftime("%H:%M") if sched else "",
        "days": sorted(scheduled_days(r), key=logic.DAY_KEYS.index),
        "created": r.created_at.date().isoformat(),
        "steps": steps,
    }
