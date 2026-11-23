"""Sanity checks for a routine: gentle "did you forget...?" tips.

Pure functions over plain dicts, so they are easy to test. A product fact is
{"name", "category", "ingredients": [lowercase names], "expiry": expiry.info(...)|None,
 "finished": bool}.
"""

RETINOIDS = ("retinol", "retinal", "retinaldehyde", "tretinoin", "adapalene", "trifarotene", "retinyl")
DAYTIME = ("morning", "afternoon")


def _is_sunscreen(p):
    cat, name = p["category"].lower(), p["name"].lower()
    return "sunscreen" in cat or "spf" in cat or "spf" in name or "sunscreen" in name


def _has_retinoid(p):
    return any(any(r in ing for r in RETINOIDS) for ing in p["ingredients"])


def _check(key, severity, icon, title, text, tip=""):
    return {"key": key, "severity": severity, "icon": icon, "title": title, "text": text, "tip": tip}


def routine_checks(slot, products):
    """Tips for one routine. severity: "warn" (worth fixing) or "info"."""
    slot = (slot or "").lower()
    if not products:
        return []
    out = []

    if slot == "morning" and not any(_is_sunscreen(p) for p in products):
        out.append(_check(
            "no-spf", "warn", "☀️", "No sunscreen in this morning routine",
            "Daytime skin needs SPF as the very last step, even on cloudy days.",
            "Add a sunscreen from your shelf, or pick one up from the shopping list.",
        ))

    if slot in DAYTIME:
        for p in products:
            if _has_retinoid(p):
                out.append(_check(
                    "retinoid-day", "warn", "🌙", f"{p['name']} is better at night",
                    "Retinoids can make skin more sun-sensitive, and light breaks some of them down.",
                    "Move it to an evening routine and keep SPF for the morning.",
                ))

    if slot == "evening" and not any("cleanser" in p["category"].lower() for p in products):
        out.append(_check(
            "no-cleanser", "info", "🫧", "No cleanser in this evening routine",
            "Evenings are when sunscreen, sweat and makeup need to come off.",
            "Start with a cleanser so the rest of your steps can reach your skin.",
        ))

    for p in products:
        ex = p.get("expiry")
        if p.get("finished"):
            out.append(_check("finished", "warn", "🧴", f"{p['name']} is finished",
                              "You marked it as used up.", "Restock it or swap it for something else."))
        elif ex and ex["state"] == "expired":
            out.append(_check("expired", "warn", "⏳", f"{p['name']} has expired",
                              f"{ex['label']}. Old products can lose strength or irritate skin.",
                              "Swap it out. It's on your shopping list."))
        elif ex and ex["state"] == "soon":
            out.append(_check("expiring", "info", "⏳", f"{p['name']} expires soon",
                              f"{ex['label']}.", "Plan a replacement before it runs out."))
    return out
