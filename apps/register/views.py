from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home:home")

    if request.method == "POST":
        data = {
            "first_name": request.POST.get("first_name", "").strip(),
            "last_name": request.POST.get("last_name", "").strip(),
            "username": request.POST.get("username", "").strip(),
            "email": request.POST.get("email", "").strip().lower(),
        }
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        def fail(msg):
            return render(request, "register/register.html", {"error": msg, "form": data})

        if password != confirm_password:
            return fail("Passwords do not match.")

        if User.objects.filter(username__iexact=data["username"]).exists():
            return fail("That username is already taken.")

        if User.objects.filter(email__iexact=data["email"]).exists():
            return fail("An account with that email already exists.")

        candidate = User(**data)
        try:
            validate_password(password, candidate)
        except ValidationError as e:
            return fail(" ".join(e.messages))

        user = User.objects.create_user(password=password, **data)
        login(request, user)
        messages.success(request, f"Welcome to Face Value, {user.first_name}!")
        return redirect("home:home")

    return render(request, "register/register.html")
