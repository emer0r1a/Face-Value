from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.routine_builder.models import Routine

from . import logic
from .models import RoutineLog
from .services import DONE, WINDOW, active_routines, build_summary, plain_routines, routine_payload


@login_required
def tracker_view(request):
    user = request.user
    today = timezone.localdate()
    routines = active_routines(user)
    summary, logs = build_summary(user, today, routines)

    return render(request, "routine_tracker/tracker.html", {
        "tracker_data": {
            "today": today.isoformat(),
            "window": WINDOW,
            "routines": [routine_payload(r) for r in routines],
            "logs": {d.isoformat(): sorted(ids) for d, ids in logs.items()},
            "summary": summary,
            "log_url": reverse("routine_tracker:log"),
            "builder_url": reverse("routine_builder:create"),
        },
        "has_routines": bool(routines),
        "builder_url": reverse("routine_builder:create"),
    })


@login_required
@require_POST
def log_view(request):
    """Check a routine in (or out) for today or one of the last few days."""
    user = request.user
    today = timezone.localdate()
    routine = get_object_or_404(Routine, pk=request.POST.get("routine", "0"), user=user)

    try:
        day = date.fromisoformat(request.POST.get("date", today.isoformat()))
    except ValueError:
        return JsonResponse({"ok": False, "error": "That date isn't valid."}, status=400)
    if day > today or day <= today - timedelta(days=WINDOW):
        return JsonResponse({"ok": False, "error": f"You can edit the last {WINDOW} days."}, status=400)

    plain = plain_routines([routine])[0]
    if not logic.due_on(plain, day):
        return JsonResponse({"ok": False, "error": "That routine isn't scheduled for that day."}, status=400)

    done = request.POST.get("done") == "1"
    logs = RoutineLog.objects.filter(routine=routine, user=user, log_date=day)
    if done:
        if logs.exists():
            logs.update(status=DONE, completed_at=timezone.now())
        else:
            RoutineLog.objects.create(
                routine=routine, user=user, log_date=day,
                status=DONE, completed_at=timezone.now(),
            )
    else:
        logs.update(status="pending", completed_at=None)

    summary, recent = build_summary(user, today)
    return JsonResponse({
        "ok": True,
        "done": done,
        "date": day.isoformat(),
        "done_ids": sorted(recent.get(day, [])),
        "summary": summary,
    })
