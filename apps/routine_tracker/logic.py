"""Pure tracker logic: no Django imports, so it is easy to test.

Terms
- routine: a dict {"id", "days", "created"}. ``days`` is a set of day keys
  ("mon" .. "sun"); an empty set means "every day". ``created`` is a date.
- logs: {date: [routine ids completed that day]}.
"""
from datetime import timedelta

DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# (key, title, emoji, tone, description, kind, goal)
BADGES = [
    ("first", "First sprout", "🌱", "lime", "Check in your first routine.", "total", 1),
    ("streak3", "Rooted", "🌿", "lime", "Keep a 3-day streak.", "streak", 3),
    ("streak7", "Week warrior", "🌻", "sun", "Keep a 7-day streak.", "streak", 7),
    ("streak14", "In bloom", "🌸", "pink", "Keep a 14-day streak.", "streak", 14),
    ("streak30", "Evergreen", "🌳", "lime", "Keep a 30-day streak.", "streak", 30),
    ("perfect", "Perfect week", "⭐", "sun", "Finish every routine due in a full Mon-Sun week.", "perfect", 1),
    ("total25", "Regular", "💧", "sky", "Check in 25 routines.", "total", 25),
    ("total100", "Century", "🏆", "lav", "Check in 100 routines.", "total", 100),
]


def due_on(routine, day):
    """Is this routine due on ``day``? Not before it was created."""
    created = routine.get("created")
    if created and day < created:
        return False
    days = routine.get("days")
    return not days or DAY_KEYS[day.weekday()] in days


def day_stats(routines, logs, day):
    """(due, done) counts for one day."""
    due = [r for r in routines if due_on(r, day)]
    finished = set(logs.get(day, ()))
    return len(due), sum(1 for r in due if r["id"] in finished)


def required_weekdays(routines):
    """Weekday numbers (Mon=0) on which at least one routine is due, or None
    when every day counts (no routines, or one with no schedule)."""
    if not routines:
        return None
    needed = set()
    for r in routines:
        if not r.get("days"):
            return None
        needed.update(DAY_KEYS.index(k) for k in r["days"] if k in DAY_KEYS)
    return needed or None


def streaks(dates, today, required=None):
    """(current, best) streak, in days checked in.

    Days with nothing scheduled neither add to nor break a streak. A missed
    scheduled day breaks it, except today, which is still pending.
    """
    if not dates:
        return 0, 0
    run = best = 0
    day = min(dates)
    while day <= today:
        if day in dates:
            run += 1
            best = max(best, run)
        elif (required is None or day.weekday() in required) and day != today:
            run = 0
        day += timedelta(days=1)
    return run, best


def consistency(routines, logs, today, span):
    """Percent of due routines completed over the last ``span`` days."""
    due = done = 0
    for i in range(span):
        d, n = day_stats(routines, logs, today - timedelta(days=i))
        due += d
        done += n
    return round(100 * done / due) if due else 0


def perfect_week(routines, logs, today, weeks=12):
    """True if some fully elapsed Mon-Sun week had every due routine done
    (and at least three days with something due)."""
    monday = today - timedelta(days=today.weekday())
    for w in range(weeks):
        start = monday - timedelta(days=7 * w)
        if start + timedelta(days=6) > today:
            continue
        busy = ok = 0
        for i in range(7):
            due, done = day_stats(routines, logs, start + timedelta(days=i))
            if due:
                busy += 1
                ok += done >= due
        if busy >= 3 and ok == busy:
            return True
    return False


def badges(best, total, perfect):
    out = []
    for key, title, emoji, tone, desc, kind, goal in BADGES:
        value = {"streak": best, "total": total, "perfect": 1 if perfect else 0}[kind]
        out.append({
            "key": key, "title": title, "emoji": emoji, "tone": tone, "desc": desc,
            "kind": kind, "goal": goal, "value": min(value, goal), "unlocked": value >= goal,
        })
    return out


def summary(routines, logs, today, dates=None, total=None):
    """Everything the tracker page shows as numbers.

    ``dates`` / ``total`` default to what ``logs`` holds; pass the full
    history when ``logs`` is only a recent window.
    """
    if dates is None:
        dates = {d for d, ids in logs.items() if ids}
    if total is None:
        total = sum(len(set(ids)) for ids in logs.values())
    current, best = streaks(dates, today, required_weekdays(routines))
    return {
        "current": current,
        "best": best,
        "total": total,
        "week_pct": consistency(routines, logs, today, 7),
        "month_pct": consistency(routines, logs, today, 30),
        "badges": badges(best, total, perfect_week(routines, logs, today)),
    }
