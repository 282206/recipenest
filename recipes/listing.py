"""Filtering and sorting shared by the home page and the JSON search API,
so the jQuery results and the server-rendered page always agree."""
from django.db.models import Q

from .models import CUISINE_NAMES, Recipe

SORTS = [("rec", "Recommended"), ("quick", "Quickest first"), ("az", "A to Z")]
TYPES = [("all", "All"), ("veg", "Veg"), ("nonveg", "Non-veg")]


def read_filters(params):
    """Clean ?q=&type=&cuisine=&sort= values from request.GET."""
    q = params.get("q", params.get("ing", "")).strip()[:100]
    kind = params.get("type", "all")
    cuisine = params.get("cuisine", "all")
    sort = params.get("sort", "rec")
    return {
        "q": q,
        "type": kind if kind in dict(TYPES) else "all",
        "cuisine": cuisine if cuisine in CUISINE_NAMES else "all",
        "sort": sort if sort in dict(SORTS) else "rec",
    }


def round_robin(recipes):
    """Recommended order: one recipe from each cuisine in turn, so the grid shows variety."""
    groups = {}
    for recipe in sorted(recipes, key=lambda r: r.id):
        groups.setdefault(recipe.cuisine, []).append(recipe)
    order = [name for name in CUISINE_NAMES if name in groups] + [n for n in groups if n not in CUISINE_NAMES]
    result = []
    while len(result) < len(recipes):
        for name in order:
            if groups[name]:
                result.append(groups[name].pop(0))
    return result


def filtered_recipes(filters):
    """Return a list of recipes matching the filters, in the chosen order."""
    recipes = Recipe.objects.all()
    if filters["q"]:
        q = filters["q"]
        recipes = recipes.filter(Q(ingredients__icontains=q) | Q(title__icontains=q) | Q(cuisine__icontains=q))
    if filters["type"] != "all":
        recipes = recipes.filter(is_veg=filters["type"] == "veg")
    if filters["cuisine"] != "all":
        recipes = recipes.filter(cuisine=filters["cuisine"])

    if filters["sort"] == "quick":
        return list(recipes.order_by("cook_time", "title"))
    if filters["sort"] == "az":
        return list(recipes.order_by("title"))
    return round_robin(list(recipes))


def is_filtering(filters):
    return bool(filters["q"]) or filters["type"] != "all" or filters["cuisine"] != "all"


def grid_title(filters):
    if filters["q"]:
        return "Search results"
    if filters["cuisine"] != "all":
        return f"{filters['cuisine']} recipes"
    return "All recipes"


def result_label(count, filters):
    kind = {"veg": " veg", "nonveg": " non-veg"}.get(filters["type"], "")
    label = f"{count}{kind} {'recipe' if count == 1 else 'recipes'}"
    if filters["q"]:
        label += f" for “{filters['q']}”"
    return label
