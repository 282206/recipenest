import json
import random
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Avg, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import RatingForm, RecipeForm
from .listing import (SORTS, TYPES, filtered_recipes, grid_title, is_filtering,
                      read_filters, result_label)
from .models import CUISINES, Rating, Recipe, cuisine_info

PER_PAGE = 24
HERO_PICKS = ["Masala Dosa", "Margherita Pizza", "Vegetable Sushi Rolls", "Pad Thai",
              "Paneer Butter Masala", "Chicken Tacos"]
POPULAR_SEARCHES = ["paneer", "chicken", "noodles", "pasta", "cheese", "rice"]


def home_url(filters, anchor="#all-recipes", **changes):
    """Home page link for these filters, leaving out default values."""
    values = {**filters, **changes}
    defaults = {"q": "", "type": "all", "cuisine": "all", "sort": "rec", "page": 1}
    params = {k: v for k, v in values.items() if k in defaults and v != defaults[k]}
    return reverse("home") + ("?" + urlencode(params) if params else "") + anchor


def cuisine_counts():
    """[(info, count)] for every cuisine that has at least one recipe, in the standard order."""
    counts = dict(Recipe.objects.values_list("cuisine").annotate(n=Count("id")))
    return [(cuisine_info(name), counts[name]) for name, _, _ in CUISINES if counts.get(name)]


def rating_summary(title):
    """Average stars from the shared `ratings` table (CGI page), or None."""
    try:
        result = Rating.objects.filter(recipe=title).aggregate(avg=Avg("stars"), count=Count("id"))
    except DatabaseError:   # ratings table not created yet
        return None
    return result if result["count"] else None


# ---------------- Pages ----------------

def home(request):
    filters = read_filters(request.GET)
    results = filtered_recipes(filters)
    page_obj = Paginator(results, PER_PAGE).get_page(request.GET.get("page"))
    all_recipes = list(Recipe.objects.order_by("id"))
    counts = cuisine_counts()

    with_photo = [r for r in all_recipes if r.photo_url()]
    pool = with_photo or all_recipes
    pick = pool[timezone.localdate().toordinal() % len(pool)] if pool else None
    by_title = {r.title: r for r in with_photo}
    hero_photos = [by_title[t] for t in HERO_PICKS if t in by_title][:3]

    tiles = [{"name": "all", "label": "All", "emoji": "🌍", "tint": "var(--steel)", "count": len(all_recipes),
              "active": filters["cuisine"] == "all", "url": home_url(filters, cuisine="all")}]
    for info, count in counts:
        active = filters["cuisine"] == info["name"]
        tiles.append({**info, "label": info["name"], "count": count, "active": active,
                      "url": home_url(filters, cuisine="all" if active else info["name"])})

    context = {
        "filters": filters,
        "page_obj": page_obj,
        "grid_title": grid_title(filters),
        "result_label": result_label(len(results), filters),
        "filtering": is_filtering(filters),
        "active_cuisine": cuisine_info(filters["cuisine"]) if filters["cuisine"] != "all" else None,
        "clear_cuisine_url": home_url(filters, cuisine="all"),
        "type_links": [{"value": v, "label": label, "active": filters["type"] == v,
                        "url": home_url(filters, type=v)} for v, label in TYPES],
        "sorts": SORTS,
        "next_page_url": home_url(filters, page=page_obj.next_page_number()) if page_obj.has_next() else "",
        "tiles": tiles,
        "total_recipes": len(all_recipes),
        "total_cuisines": len(counts),
        "hero_photos": hero_photos if len(hero_photos) == 3 else [],
        "popular_searches": [(word, home_url(filters, q=word)) for word in POPULAR_SEARCHES],
        "pick": pick,
        "quick": Recipe.objects.filter(cook_time__lte=20).order_by("cook_time", "id")[:12],
    }
    return render(request, "recipes/home.html", context)


def detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    similar = list(Recipe.objects.filter(cuisine=recipe.cuisine).exclude(pk=pk).order_by("id")[:4])
    fill = []
    if len(similar) < 4:
        fill = list(Recipe.objects.exclude(cuisine=recipe.cuisine).exclude(pk=pk)
                    .filter(is_veg=recipe.is_veg).order_by("id")[:4 - len(similar)])
    return render(request, "recipes/detail.html", {
        "recipe": recipe,
        "cuisine": recipe.cuisine_info(),
        "rating": rating_summary(recipe.title),
        "more": similar + fill,
        "more_title": "More recipes to try" if fill else f"More {recipe.cuisine} recipes",
        "cuisine_url": home_url({}, cuisine=recipe.cuisine),
    })


def surprise(request):
    """Surprise me: open a random recipe (skipping the one just shown, if given)."""
    ids = list(Recipe.objects.values_list("id", flat=True))
    if not ids:
        messages.info(request, "Add a recipe first.")
        return redirect("home")
    last = request.GET.get("not", "")
    choices = [i for i in ids if str(i) != last] or ids
    return redirect("detail", pk=random.choice(choices))


def saved(request):
    """Saved recipes: favorites.js fills the grid from localStorage + /api/recipes/?ids=..."""
    return render(request, "recipes/saved.html")


def add_recipe(request):
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save()
            messages.success(request, f"Recipe “{recipe.title}” added.")
            return redirect("detail", pk=recipe.pk)
    else:
        form = RecipeForm()
    return render(request, "recipes/form.html", {"form": form, "mode": "add"})


def edit_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, "Changes saved.")
            return redirect("detail", pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)
    return render(request, "recipes/form.html", {"form": form, "mode": "edit", "recipe": recipe})


def delete_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        title = recipe.title
        recipe.delete()
        messages.success(request, f"Recipe “{title}” deleted.")
        return redirect("home")
    return render(request, "recipes/confirm_delete.html", {"recipe": recipe})


def browse(request):
    """Quick browse page (AngularJS). Online version of node-board/."""
    return render(request, "recipes/browse.html", {"cuisines": CUISINES})


def rate(request):
    """Rate a recipe. Online version of the CGI page in cgi-feedback/."""
    if request.method == "POST":
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save()
            messages.success(request, f"Thanks, {rating.name}. Your rating for {rating.recipe} is saved.")
            return redirect("rate")
    else:
        form = RatingForm(initial={"recipe": request.GET.get("recipe", "")})
    return render(request, "recipes/rate.html", {"form": form, "ratings": Rating.objects.all()})


# ---------------- JSON API ----------------

def api_recipes(request):
    """All recipes as JSON - used by the AngularJS Quick Browse page.
    /api/recipes/?ids=3,1,7 returns just those recipes, in that order (Saved page)."""
    recipes = Recipe.objects.order_by("title")
    ids_param = request.GET.get("ids")
    if ids_param is not None:
        ids = [int(part) for part in ids_param.split(",") if part.strip().isdigit()][:200]
        found = {r.id: r for r in Recipe.objects.filter(id__in=ids)}
        recipes = [found[i] for i in dict.fromkeys(ids) if i in found]
    data = [r.to_dict(request) for r in recipes]
    return JsonResponse({"count": len(data), "recipes": data})


def api_search(request):
    """AJAX search: /api/search/?ing=paneer&type=veg&cuisine=Indian&sort=quick"""
    filters = read_filters(request.GET)
    data = [r.to_dict(request) for r in filtered_recipes(filters)]
    return JsonResponse({
        "query": filters["q"],
        "filters": filters,
        "count": len(data),
        "title": grid_title(filters),
        "label": result_label(len(data), filters),
        "recipes": data,
    })


def export_json(request):
    """Download every recipe as a JSON file (json.dumps from Python)."""
    data = [
        {
            "title": r.title,
            "is_veg": r.is_veg,
            "cook_time": r.cook_time,
            "cuisine": r.cuisine,
            "wiki_title": r.wiki_title,
            "image_url": r.image_url,
            "ingredients": r.ingredient_list(),
            "steps": r.step_list(),
        }
        for r in Recipe.objects.order_by("id")
    ]
    response = HttpResponse(json.dumps(data, indent=2, ensure_ascii=False),
                            content_type="application/json")
    response["Content-Disposition"] = 'attachment; filename="recipenest_export.json"'
    return response
