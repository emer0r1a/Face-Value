def navbar_counts(request):
    """Unread counters shown on the floating navbar."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    from apps.ingredient_checker.models import IngredientAlert
    from apps.notifications.models import Notification

    unread = (
        Notification.objects.filter(user=user, is_read=False).count()
        + IngredientAlert.objects.filter(user=user, is_read=False).count()
    )
    return {"nav_unread_count": unread}
