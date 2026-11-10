"""
python manage.py fetch_photos
Asks the Wikipedia API for each recipe's article photo and saves the link in
image_url. Recipes with an uploaded photo are skipped. Uses only urllib + json.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand
from django.db.models import Q

from recipes.models import Recipe

API = "https://en.wikipedia.org/w/api.php"
BATCH = 40
USER_AGENT = "RecipeNest/1.0 (Web Technologies AIM3140 student project; Django management command)"


def fetch_thumbnails(titles):
    """Return {requested title: thumbnail url} for one batch of Wikipedia titles."""
    params = {
        "action": "query", "format": "json", "redirects": "1",
        "prop": "pageimages", "piprop": "thumbnail", "pithumbsize": "800", "pilimit": "50",
        "titles": "|".join(titles),
    }
    request = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        query = json.load(response).get("query", {})

    # Wikipedia may rename a title (normalized) and then follow a redirect;
    # map each name to the next one so every requested title reaches its page.
    alias = {}
    for step in query.get("normalized", []) + query.get("redirects", []):
        alias[step["from"]] = step["to"]
    thumbs = {page["title"]: page["thumbnail"]["source"]
              for page in query.get("pages", {}).values() if "thumbnail" in page}

    found = {}
    for title in titles:
        final = title
        for _ in range(3):
            if final not in alias:
                break
            final = alias[final]
        if final in thumbs:
            found[title] = thumbs[final]
    return found


class Command(BaseCommand):
    help = "Fill image_url with photos from Wikipedia for recipes that have no uploaded photo"

    def add_arguments(self, parser):
        parser.add_argument("--refresh", action="store_true",
                            help="Also replace links that are already filled in")

    def handle(self, *args, **options):
        no_upload = Q(image="") | Q(image__isnull=True)
        recipes = Recipe.objects.exclude(wiki_title="").filter(no_upload)
        if not options["refresh"]:
            recipes = recipes.filter(image_url="")
        recipes = list(recipes)
        titles = sorted({r.wiki_title for r in recipes})
        if not titles:
            self.stdout.write("Every recipe already has a photo. Use --refresh to fetch them again.")
            return

        photos = {}
        for start in range(0, len(titles), BATCH):
            batch = titles[start:start + BATCH]
            try:
                photos.update(fetch_thumbnails(batch))
            except (urllib.error.URLError, TimeoutError, ValueError) as err:
                self.stderr.write(f"Couldn't reach Wikipedia for {len(batch)} titles: {err}")

        saved = 0
        for recipe in recipes:
            url = photos.get(recipe.wiki_title)
            if url and len(url) <= 500:
                recipe.image_url = url
                recipe.save(update_fields=["image_url"])
                saved += 1
        missing = sorted(r.title for r in recipes if r.wiki_title not in photos)
        self.stdout.write(self.style.SUCCESS(f"Saved Wikipedia photos for {saved} of {len(recipes)} recipes."))
        if missing:
            self.stdout.write("No photo found for: " + ", ".join(missing))
