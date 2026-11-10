from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Profile


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name()
        }
    )

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name", "")
        profile.bio = request.POST.get("bio", "")

        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES["profile_image"]

        profile.save()

        return redirect("user_profile:profile")

    return render(request, "user_profile/user_profile.html", {
        "profile": profile
    })