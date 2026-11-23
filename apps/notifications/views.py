from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from .models import Notification


@login_required
@require_POST
def dismiss_view(request, pk):
    """Mark one notification as read, then go back where the user was."""
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    note.is_read = True
    note.save(update_fields=["is_read"])
    nxt = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(nxt, {request.get_host()}):
        nxt = "/home/"
    return redirect(nxt)


@login_required
@require_POST
def mark_read_view(request, pk):
    """AJAX: mark a single notification read. Returns JSON."""
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    note.is_read = True
    note.save(update_fields=["is_read"])
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"ok": True, "unread": unread})


@login_required
@require_POST
def mark_all_read_view(request):
    """Mark every unread notification as read."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    nxt = request.POST.get("next", "")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "unread": 0})
    if not url_has_allowed_host_and_scheme(nxt, {request.get_host()}):
        nxt = "/notifications/"
    return redirect(nxt)


@login_required
@require_GET
def poll_view(request):
    """
    Lightweight polling endpoint called by the frontend every ~30 s.
    Returns notifications created in the last 2 minutes that are still unread
    (these become toast pop-ups), plus the total unread count.
    """
    since_str = request.GET.get("since")  # ISO timestamp from last poll
    user = request.user

    # Total unread for the bell badge
    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    # New notifications since the last poll (for toast pop-ups)
    if since_str:
        try:
            from datetime import datetime
            since_dt = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
        except ValueError:
            since_dt = timezone.now() - timezone.timedelta(minutes=2)
    else:
        since_dt = timezone.now() - timezone.timedelta(minutes=2)

    fresh = list(
        Notification.objects.filter(
            user=user,
            is_read=False,
            created_at__gte=since_dt,
        ).values("id", "title", "message", "url", "icon", "notification_type", "created_at")[:5]
    )
    # Serialize datetimes
    for n in fresh:
        n["created_at"] = n["created_at"].isoformat()

    return JsonResponse({"unread": unread_count, "fresh": fresh})


@login_required
def inbox_view(request):
    """Full notification centre page."""
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")[:60]
    unread_count = sum(1 for n in notifications if not n.is_read)
    return render(request, "notifications/inbox.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })

