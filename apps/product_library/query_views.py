"""Two pages built around the SQL features required for the final project.

1. Ingredient overview  ->  JOIN      (ProductIngredient + Product + Ingredient)
2. Not in any routine   ->  SUBQUERY  (Product NOT IN (SELECT product_id FROM RoutineItem))

Each view also builds a readable copy of the SQL Django generates, so the
query can be shown on screen and pasted into the Supabase SQL Editor.
"""
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Subquery
from django.shortcuts import render

from apps.ingredient_checker.services import is_classified
from apps.routine_builder.models import RoutineItem

from .models import Product, ProductIngredient
from .views import art_for

TONES = ["lime", "sky", "pink", "sun", "lav"]


# --------------------------------------------------------------- SQL display
def _literal(value):
    """Render a query parameter as a SQL literal (so the SQL is runnable)."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _filled_sql(queryset):
    """The statement Django runs, with the parameter values filled in."""
    sql, params = queryset.query.sql_with_params()
    params = iter(params)
    parts = re.split(r"(%s|%%)", sql)
    return "".join(
        _literal(next(params)) if part == "%s" else ("%" if part == "%%" else part)
        for part in parts
    )


def _pretty(sql):
    """One clause per line, with a subquery indented under its parent."""
    sql = re.sub(r"\s+", " ", sql).strip()
    sql = re.sub(r" (FROM|WHERE|ORDER BY|GROUP BY) ", r"\n\1 ", sql)
    sql = re.sub(r" (INNER JOIN|LEFT OUTER JOIN) ", r"\n\1 ", sql)
    sql = re.sub(r" (AND|OR) ", r"\n  \1 ", sql)
    sql = sql.replace("(SELECT ", "(\n    SELECT ")

    out, inside = [], False
    for line in sql.split("\n"):
        if inside and not line.startswith(" "):
            line = "    " + line
        out.append(line)
        if line.rstrip().endswith("("):
            inside = True
        elif inside and line.count(")") > line.count("("):
            inside = False
    return "\n".join(out)


def sql_panel(queryset, label, note=""):
    """The SQL for `queryset`, in a short form and in full."""
    full = _pretty(_filled_sql(queryset))
    # Django lists every column of every joined table. The short form folds
    # only that first column list so the JOIN / WHERE structure is easy to see.
    head = re.match(r"^SELECT (.*?)\nFROM ", full, flags=re.S)
    long_list = bool(head) and head.group(1).count(",") >= 3
    short = re.sub(r"^SELECT .*?\nFROM ", "SELECT …\nFROM ", full, count=1, flags=re.S) if long_list else full
    return {"label": label, "short": short, "full": full, "note": note}


def joined_rows(user, query=""):
    """The JOIN queryset (not evaluated yet, so its SQL can be inspected)."""
    qs = (
        ProductIngredient.objects
        .filter(product__user=user)
        .select_related("product", "ingredient")
        .order_by("ingredient__ingredient_name", "product__product_name")
    )
    if query:
        qs = qs.filter(
            Q(ingredient__ingredient_name__icontains=query)
            | Q(product__product_name__icontains=query)
            | Q(product__brand__icontains=query)
        )
    return qs


# --------------------------------------------------------------- 1. JOIN
@login_required
def ingredient_overview_view(request):
    query = request.GET.get("q", "").strip()

    # JOIN: ProductIngredient is the junction table between Product and
    # Ingredient. select_related() makes Django fetch both related rows in the
    # same SQL statement with INNER JOINs, instead of one query per row.
    rows = joined_rows(request.user, query)
    sql = sql_panel(
        rows, "INNER JOIN",
        "ProductIngredient (junction) is joined to Product and to Ingredient.",
    )

    rows = list(rows)  # runs the query
    for r in rows:
        r.known = is_classified(r.ingredient)

    return render(request, "product_library/ingredient_overview.html", {
        "rows": rows,
        "query": query,
        "row_count": len(rows),
        "ingredient_count": len({r.ingredient_id for r in rows}),
        "product_count": len({r.product_id for r in rows}),
        "sql": sql,
    })


# --------------------------------------------------------------- 2. SUBQUERY
@login_required
def unused_products_view(request):
    shelf = Product.objects.filter(user=request.user, status="active")

    # INNER query: the ids of every product that is a step in some routine.
    used_product_ids = RoutineItem.objects.order_by().values("product_id")

    # OUTER query: the shelf products whose id is NOT IN the inner result.
    # (RoutineItem.product is a required foreign key, so the inner query can
    # never return NULL, which is what makes NOT IN safe here.)
    unused_qs = shelf.exclude(id__in=Subquery(used_product_ids)).order_by("-date_added")
    in_routine_qs = shelf.filter(id__in=Subquery(used_product_ids))

    unused = list(unused_qs)
    for i, p in enumerate(unused):
        p.art = art_for(p.category)
        p.tone = TONES[i % len(TONES)]

    in_routine = in_routine_qs.count()

    return render(request, "product_library/unused_products.html", {
        "products": unused,
        "unused_count": len(unused),
        "in_routine_count": in_routine,
        "shelf_count": len(unused) + in_routine,
        "sql_inner": sql_panel(
            used_product_ids, "SUBQUERY",
            "Runs first: every product id that appears in a routine.",
        ),
        "sql_outer": sql_panel(
            unused_qs, "NOT IN (SELECT …)",
            "Uses the inner SELECT as its condition: id NOT IN ( … ).",
        ),
    })
