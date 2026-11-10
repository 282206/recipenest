"""
python manage.py load_recipes
Reads seed/recipes.json (JSON parsing in Python) and saves each recipe to MySQL.
Recipes already in the database (matched by title) are not duplicated; their
cuisine and Wikipedia title are updated from the JSON instead.
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Recipe


class Command(BaseCommand):
    help = "Load starter recipes from seed/recipes.json"

    def add_arguments(self, parser):
        parser.add_argument("--file", default=str(Path(settings.BASE_DIR) / "seed" / "recipes.json"))

    def handle(self, *args, **options):
        path = Path(options["file"])
        with open(path, encoding="utf-8") as f:
            items = json.load(f)  # JSON text -> Python list of dicts

        added = updated = 0
        for item in items:
            cuisine = item.get("cuisine", "Indian")
            wiki_title = item.get("wiki_title", "")
            existing = Recipe.objects.filter(title=item["title"]).first()
            if existing:
                if (existing.cuisine, existing.wiki_title) != (cuisine, wiki_title):
                    existing.cuisine = cuisine
                    existing.wiki_title = wiki_title
                    existing.save(update_fields=["cuisine", "wiki_title"])
                    updated += 1
                continue
            Recipe.objects.create(
                title=item["title"],
                cuisine=cuisine,
                wiki_title=wiki_title,
                ingredients="\n".join(item["ingredients"]),
                steps="\n".join(item["steps"]),
                is_veg=item["is_veg"],
                cook_time=item["cook_time"],
            )
            added += 1
        self.stdout.write(self.style.SUCCESS(
            f"Loaded {added} new recipes and updated {updated} from {path.name} "
            f"({Recipe.objects.count()} recipes in total)"
        ))
