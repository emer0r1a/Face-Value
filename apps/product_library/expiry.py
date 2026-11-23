"""Period-after-opening (PAO) maths. Pure Python, no Django, easy to test.

A product has an expiry only when we know both when it was opened and how
many months it stays good for after opening (the little jar symbol).
"""
import calendar
from datetime import date

SOON_DAYS = 30
PAO_CHOICES = [3, 6, 9, 12, 18, 24, 36]

# Typical months-after-opening by category, used as a starting suggestion.
DEFAULT_PAO = {
    "cleanser": 12, "toner": 12, "serum": 6, "moisturizer": 12,
    "sunscreen": 6, "exfoliant": 12, "mask": 12, "eye care": 6,
    "treatment": 6, "other": 12,
}


def default_pao(category):
    return DEFAULT_PAO.get((category or "").lower(), 12)


def add_months(d, months):
    index = d.month - 1 + months
    year, month = d.year + index // 12, index % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def expiry_date(opened_on, pao_months):
    if not opened_on or not pao_months:
        return None
    return add_months(opened_on, pao_months)


def info(opened_on, pao_months, today):
    """None when untracked, else {"expires_on", "days_left", "state", "label", "short"}.

    state is "expired", "soon" (within SOON_DAYS) or "ok".
    """
    expires = expiry_date(opened_on, pao_months)
    if not expires:
        return None
    left = (expires - today).days
    if left < 0:
        state, short = "expired", "Expired"
        label = f"Expired {-left} day{'s' if left != -1 else ''} ago"
    elif left <= SOON_DAYS:
        state = "soon"
        short = "Expires today" if left == 0 else f"{left}d left"
        label = "Expires today" if left == 0 else f"{left} day{'s' if left != 1 else ''} left"
    else:
        state, short = "ok", "Fresh"
        label = f"Fresh until {expires.strftime('%b %Y')}"
    return {"expires_on": expires, "days_left": left, "state": state, "label": label, "short": short}
