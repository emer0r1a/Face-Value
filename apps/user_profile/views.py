from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.product_library.models import Product, ProductReport
from apps.product_library.views import REPORT_REASONS

from .models import Profile
from .services import account_stats, image_error, remove_avatar, store_avatar, user_reports

NAME_MAX = 150
BIO_MAX = 500


def _profile(user):
    profile, _ = Profile.objects.get_or_create(
        user=user, defaults={"full_name": user.get_full_name()}
    )
    return profile


@login_required
def profile_view(request):
    user = request.user
    profile = _profile(user)
    errors = {}

    if request.method == "POST":
        name = request.POST.get("full_name", "").strip()
        bio = request.POST.get("bio", "").strip()
        photo = request.FILES.get("profile_image")

        if len(name) > NAME_MAX:
            errors["full_name"] = f"Keep your name under {NAME_MAX} characters."
        if len(bio) > BIO_MAX:
            errors["bio"] = f"Keep your bio under {BIO_MAX} characters."
        problem = image_error(photo)
        if problem:
            errors["profile_image"] = problem

        if not errors:
            profile.full_name, profile.bio = name, bio
            if request.POST.get("remove_photo") == "1" and not photo:
                remove_avatar(profile)
            if photo:
                store_avatar(profile, photo)
            profile.save()
            messages.success(request, "Profile saved.")
            return redirect("user_profile:profile")
        # keep what they typed so nothing is lost
        profile.full_name, profile.bio = name, bio

    today = timezone.localdate()
    products = list(Product.objects.filter(user=user).order_by("product_name").values("id", "product_name", "brand"))
    context = {
        "profile": profile,
        "errors": errors,
        "stats": account_stats(user, today),
        "reports": user_reports(user),
        "report_products": products,
        "report_reasons": REPORT_REASONS,
        "name_max": NAME_MAX,
        "bio_max": BIO_MAX,
        "password_form": PasswordChangeForm(user),
        "open_dialog": "",
    }
    if user.is_staff:
        context["pending_reports"] = ProductReport.objects.filter(status="pending").count()
    return render(request, "user_profile/user_profile.html", context)


@login_required
@require_POST
def password_view(request):
    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # stay signed in
        messages.success(request, "Password updated.")
        return redirect("user_profile:profile")

    today = timezone.localdate()
    profile = _profile(request.user)
    return render(request, "user_profile/user_profile.html", {
        "profile": profile, "errors": {}, "stats": account_stats(request.user, today),
        "reports": user_reports(request.user),
        "report_products": list(Product.objects.filter(user=request.user).order_by("product_name").values("id", "product_name", "brand")),
        "report_reasons": REPORT_REASONS, "name_max": NAME_MAX, "bio_max": BIO_MAX,
        "password_form": form, "open_dialog": "passwordDialog",
        **({"pending_reports": ProductReport.objects.filter(status="pending").count()} if request.user.is_staff else {}),
    }, status=400)
