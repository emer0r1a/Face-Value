from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home:home")

    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)
            return redirect("home:home")

        return render(request, "login/login.html", {
            "error": "Hmm, that username or password doesn't match.",
            "username": username,
            "next": next_url,
        })

    return render(request, "login/login.html", {"next": next_url})


def logout_view(request):
    if request.method == "POST":
        logout(request)

    return redirect("landing")
