from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

from .models import StoredFile


@require_GET
def serve_media(request, name):
    """Stream an uploaded file out of the database. Names are random UUIDs and
    never reused, so browsers can cache them for good."""
    row = StoredFile.objects.filter(name=name).first()
    if row is None:
        raise Http404("No such file.")
    resp = HttpResponse(bytes(row.data), content_type=row.content_type)
    resp["Cache-Control"] = "public, max-age=31536000, immutable"
    resp["X-Content-Type-Options"] = "nosniff"
    return resp
