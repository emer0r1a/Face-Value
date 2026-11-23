"""Database helpers shared by the library, shopping list, routines and dashboard."""
from . import expiry
from .models import Product

# Basics worth flagging when nothing active on the shelf covers them.
ESSENTIALS = ("Cleanser", "Moisturizer", "Sunscreen")


def attach_expiry(products, today):
    for p in products:
        p.expiry = expiry.info(p.opened_on, p.pao_months, today)
    return products


def shopping_items(user, today):
    """What to replace or restock, from products the user already saved."""
    products = attach_expiry(list(Product.objects.filter(user=user).order_by("product_name")), today)

    replace, soon, archived = [], [], []
    for p in products:
        if p.status == "finished":
            p.reason = "Finished"
            replace.append(p)
        elif p.status == "active" and p.expiry and p.expiry["state"] == "expired":
            p.reason = "Expired"
            replace.append(p)
        elif p.status == "active" and p.expiry and p.expiry["state"] == "soon":
            p.reason = p.expiry["label"]
            soon.append(p)
        elif p.status == "archived":
            archived.append(p)

    have = {
        (p.category or "").lower() for p in products
        if p.status == "active" and not (p.expiry and p.expiry["state"] == "expired")
    }
    gaps = [c for c in ESSENTIALS if c.lower() not in have] if products else []

    return {
        "replace": replace, "soon": soon, "archived": archived, "gaps": gaps,
        "count": len(replace) + len(soon),
    }
