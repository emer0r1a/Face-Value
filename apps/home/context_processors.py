def navbar_counts(request):
    """Unread counters for the floating navbar, plus the user's theme."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    from apps.ingredient_checker.models import IngredientAlert
    from apps.notifications.models import Notification
    from apps.user_settings.models import UserSettings

    unread = (
        Notification.objects.filter(user=user, is_read=False).count()
        + IngredientAlert.objects.filter(user=user, is_read=False).count()
    )
    dark = UserSettings.objects.filter(user=user, dark_mode=True).exists()
    return {"nav_unread_count": unread, "fv_dark_mode": dark}
