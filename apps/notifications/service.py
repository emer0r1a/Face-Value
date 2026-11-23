"""
Notification service -- the single place that creates Notification rows.

Call these helpers from views, signals, or management commands.
Each function is idempotent-ish: it won't spam the user if the same
condition fires repeatedly within the same day.
"""
from django.urls import reverse
from django.utils import timezone

from .models import Notification


# ---------------------------------------------------------------------------
# Low-level helper
# ---------------------------------------------------------------------------

def _push(user, title, message, ntype, url="", icon="", routine=None):
    """Create and return a Notification. Duplicate-guard: skip if the same
    (user, type, url) pair was already created today."""
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    already = Notification.objects.filter(
        user=user,
        notification_type=ntype,
        url=url,
        created_at__gte=today_start,
    ).exists()
    if already:
        return None
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=ntype,
        url=url,
        icon=icon,
        routine=routine,
        scheduled_at=timezone.now(),
        created_at=timezone.now(),
    )


# ---------------------------------------------------------------------------
# Trigger functions
# ---------------------------------------------------------------------------

def notify_report_update(report):
    """Tell the reporter that their product report status changed."""
    user = report.user
    product = report.product
    pname = product.product_name
    url = reverse("product_library:detail", args=[product.pk])

    if report.status == "resolved":
        title = 'Your report on "' + pname + '" was resolved'
        msg = (
            "Good news -- the Face Value team reviewed your report about "
            '"' + pname + '" (' + report.reason + ") and marked it resolved. "
            "The product listing has been updated."
        )
        icon = "\u2705"  # checkmark
    elif report.status == "dismissed":
        title = 'Your report on "' + pname + '" was reviewed'
        msg = (
            "The Face Value team looked into your report about "
            '"' + pname + '" (' + report.reason + ") but decided no changes "
            "were needed at this time."
        )
        icon = "\u2139\ufe0f"  # info
    else:
        status_label = report.status.capitalize()
        title = "Report status updated: " + status_label
        msg = 'Your report about "' + pname + '" is now ' + report.status + "."
        icon = "\U0001f4cb"  # clipboard

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    already = Notification.objects.filter(
        user=user,
        notification_type=Notification.TYPE_REPORT_UPDATE,
        url=url,
        created_at__gte=today_start,
        title=title,
    ).exists()
    if already:
        return None
    return Notification.objects.create(
        user=user,
        title=title,
        message=msg,
        notification_type=Notification.TYPE_REPORT_UPDATE,
        url=url,
        icon=icon,
        scheduled_at=timezone.now(),
        created_at=timezone.now(),
    )


def notify_expiry(user, product, state):
    """Create a freshness reminder for a product that is 'soon' or 'expired'."""
    url = reverse("product_library:detail", args=[product.pk])
    pname = product.product_name
    cat = product.category.lower()
    brand = product.brand

    if state == "expired":
        ntype = Notification.TYPE_EXPIRY_EXPIRED
        title = '"' + pname + '" has expired'
        msg = (
            "Your " + cat + ' "' + pname + '" by ' + brand + " "
            "has passed its period-after-opening date. Consider replacing it."
        )
        icon = "\U0001f5d1\ufe0f"  # wastebasket
    else:
        ntype = Notification.TYPE_EXPIRY_SOON
        title = '"' + pname + '" is expiring soon'
        msg = (
            "Your " + cat + ' "' + pname + '" by ' + brand + " "
            "is nearing its period-after-opening date. Use it up or plan to restock."
        )
        icon = "\u23f3"  # hourglass

    return _push(user, title, msg, ntype, url=url, icon=icon)


def notify_streak_milestone(user, streak):
    """Celebrate a streak milestone (7, 14, 30, 60, 100 days)."""
    milestones = {7, 14, 30, 60, 100}
    if streak not in milestones:
        return None
    title = "\U0001f525 " + str(streak) + "-day streak!"
    msg = (
        "You've completed your skincare routine for " + str(streak) + " days in a row. "
        "Consistency is the secret to glowing skin -- keep it up!"
    )
    return _push(
        user, title, msg,
        Notification.TYPE_STREAK,
        url=reverse("routine_tracker:tracker"),
        icon="\U0001f525",
    )


def notify_welcome(user):
    """One-time welcome notification on first login / registration."""
    return _push(
        user,
        "Welcome to Face Value! \U0001f44b",
        "Your skincare companion is ready. Add your first product, build a routine, "
        "and let Face Value help you track what works for your skin.",
        Notification.TYPE_WELCOME,
        url=reverse("product_library:add"),
        icon="\U0001f44b",
    )


def check_and_notify_expiry(user, products, today):
    """Call on dashboard load to surface freshness reminders once per day."""
    from apps.product_library import expiry as exp_mod
    for product in products:
        if product.status != "active":
            continue
        info = exp_mod.info(product.opened_on, product.pao_months, today)
        if info and info["state"] in ("soon", "expired"):
            notify_expiry(user, product, info["state"])
