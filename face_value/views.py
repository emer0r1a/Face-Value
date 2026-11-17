from django.shortcuts import redirect, render


def landing_view(request):
    """Public landing page. Signed-in users go straight to their dashboard."""
    if request.user.is_authenticated:
        return redirect("home:home")
    return render(request, "home/landing.html")
