from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .views import login_view, logout_view

app_name = "login"

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Forgot password: ask for an email, send a one-time link, set a new password.
    path("forgot/", auth_views.PasswordResetView.as_view(
        template_name="login/forgot.html",
        email_template_name="login/reset_email.txt",
        subject_template_name="login/reset_subject.txt",
        success_url=reverse_lazy("login:forgot_sent"),
    ), name="forgot"),
    path("forgot/sent/", auth_views.PasswordResetDoneView.as_view(
        template_name="login/forgot_sent.html",
    ), name="forgot_sent"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="login/reset_confirm.html",
        success_url=reverse_lazy("login:reset_done"),
    ), name="reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="login/reset_done.html",
    ), name="reset_done"),
]
