"""File storage that keeps uploads in the database instead of on local disk.

Uploaded photos used to be written to ./media, which only exists on one
machine, so opening the app from another device (or after a redeploy) showed
broken images. Every ImageField now saves into the StoredFile table and is
served by `serve_media` at /media/<name>.
"""
import mimetypes
from urllib.parse import quote

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    def _model(self):
        from .models import StoredFile  # imported late: settings load before apps
        return StoredFile

    def _open(self, name, mode="rb"):
        row = self._model().objects.filter(name=name).first()
        if row is None:
            raise FileNotFoundError(name)
        return ContentFile(bytes(row.data), name=name)

    def _save(self, name, content):
        content.seek(0)
        data = content.read()
        self._model().objects.update_or_create(name=name, defaults={
            "data": data,
            "size": len(data),
            "content_type": mimetypes.guess_type(name)[0] or "application/octet-stream",
        })
        return name

    def exists(self, name):
        return self._model().objects.filter(name=name).exists()

    def delete(self, name):
        if name:
            self._model().objects.filter(name=name).delete()

    def size(self, name):
        return self._model().objects.values_list("size", flat=True).get(name=name)

    def url(self, name):
        return settings.MEDIA_URL + quote(name)
