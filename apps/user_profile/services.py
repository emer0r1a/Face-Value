"""Profile helpers: avatar processing and the little numbers on the profile."""
import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

from apps.product_library.models import Product, ProductReport
from apps.product_library.views import _image_error as image_error  # noqa: F401 (re-exported)
from apps.routine_builder.models import Routine
from apps.routine_tracker.logic import streaks
from apps.routine_tracker.services import load_history, required_weekdays

AVATAR_SIZE = 480


def store_avatar(profile, upload):
    """Crop to a square, shrink and re-encode (this also drops EXIF/GPS data)."""
    img = ImageOps.exif_transpose(Image.open(upload))
    img = ImageOps.fit(img.convert("RGB"), (AVATAR_SIZE, AVATAR_SIZE))
    buf = BytesIO()
    img.save(buf, "JPEG", quality=86, optimize=True)
    remove_avatar(profile)
    profile.profile_image.save(f"{uuid.uuid4().hex}.jpg", ContentFile(buf.getvalue()), save=False)


def remove_avatar(profile):
    if profile.profile_image:
        profile.profile_image.storage.delete(profile.profile_image.name)
        profile.profile_image = None


def account_stats(user, today):
    _, dates, total = load_history(user, today)
    current, best = streaks(set(dates), today, required_weekdays(user))
    return {
        "products": Product.objects.filter(user=user).count(),
        "routines": Routine.objects.filter(user=user).count(),
        "checkins": total,
        "streak": current,
        "best": best,
    }


def user_reports(user, limit=8):
    return list(
        ProductReport.objects.filter(user=user)
        .select_related("product").order_by("-reported_at")[:limit]
    )
