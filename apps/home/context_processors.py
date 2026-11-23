def navbar_counts(request):
    """Unread counters for the floating navbar, plus the user's theme."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    from apps.ingredient_checker.models import IngredientAlert
    from apps.notifications.models import Notification
    from apps.user_settings.models import UserSettings
    from apps.user_profile.models import Profile

    unread = (
        Notification.objects.filter(user=user, is_read=False).count()
        + IngredientAlert.objects.filter(user=user, is_read=False).count()
    )
    dark = UserSettings.objects.filter(user=user, dark_mode=True).exists()

    nav_profile_image = None
    try:
        profile = Profile.objects.get(user=user)
        if profile.profile_image:
            nav_profile_image = profile.profile_image.url
    except Profile.DoesNotExist:
        pass

    return {"nav_unread_count": unread, "fv_dark_mode": dark, "nav_profile_image": nav_profile_image}
