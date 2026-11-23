from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
@require_POST
def dismiss_view(request, pk):
    """Mark one reminder as read, then go back where the user was."""
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    note.is_read = True
    note.save(update_fields=["is_read"])
    nxt = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(nxt, {request.get_host()}):
        nxt = "/home/"
    return redirect(nxt)
