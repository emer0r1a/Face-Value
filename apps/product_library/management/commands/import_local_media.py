from django.conf import settings
from django.core.management.base import BaseCommand

from apps.product_library.models import StoredFile
import mimetypes


class Command(BaseCommand):
    help = "Copy photos already saved in the local media/ folder into the database."

    def handle(self, *args, **opts):
        root = settings.MEDIA_ROOT
        if not root.exists():
            self.stdout.write("No local media folder, nothing to import.")
            return
        added = skipped = 0
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            name = path.relative_to(root).as_posix()
            if StoredFile.objects.filter(name=name).exists():
                skipped += 1
                continue
            data = path.read_bytes()
            StoredFile.objects.create(
                name=name, data=data, size=len(data),
                content_type=mimetypes.guess_type(name)[0] or "application/octet-stream",
            )
            added += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {added} file(s), skipped {skipped} already in the database."))
