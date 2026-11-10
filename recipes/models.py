import re
from urllib.parse import quote

from django.db import models

# Cuisine name, emoji and tile colour (same list as the design reference)
CUISINES = [
    ("Indian", "🍛", "#FBE3C4"),
    ("Italian", "🍝", "#F9DCD5"),
    ("Chinese", "🥟", "#F7E0C9"),
    ("Indo-Chinese", "🥡", "#F3E2D2"),
    ("Japanese", "🍣", "#FADDE4"),
    ("Thai", "🌶️", "#DDEFD8"),
    ("Korean", "🍚", "#E6E1F5"),
    ("Mexican", "🌮", "#FBE7BE"),
    ("Middle Eastern", "🧆", "#EEE4CC"),
    ("French", "🥐", "#F6E6CF"),
    ("Spanish", "🥘", "#FADCC8"),
    ("Greek", "🫒", "#E0ECD6"),
    ("British", "🫖", "#E2E6EE"),
    ("American", "🍔", "#F8DFC8"),
    ("Other", "🍽️", "#E9ECEA"),
]
CUISINE_NAMES = [name for name, _, _ in CUISINES]
CUISINE_CHOICES = [(name, name) for name in CUISINE_NAMES]
_CUISINE_INFO = {name: {"name": name, "emoji": emoji, "tint": tint} for name, emoji, tint in CUISINES}


def cuisine_info(name):
    """{'name', 'emoji', 'tint'} for a cuisine; unknown names fall back to Other's look."""
    return _CUISINE_INFO.get(name) or {"name": name or "Other", "emoji": "🍽️", "tint": "#E9ECEA"}


# "200 g paneer, cubed" -> "paneer" (used for the "You'll need ..." line)
_QUANTITY = re.compile(
    r"^[\d/\s½¼¾.]+(g|kg|ml|cups?|tbsp|tsp|inch|pinch|bunch(es)?|slices?|cloves?|pieces?)?\s+", re.IGNORECASE
)


class Recipe(models.Model):
    title = models.CharField(max_length=120)
    cuisine = models.CharField(max_length=20, choices=CUISINE_CHOICES, default="Indian")
    ingredients = models.TextField(help_text="One ingredient per line")
    steps = models.TextField(help_text="One step per line")
    image = models.ImageField(upload_to="recipes/", blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, help_text="Photo link (filled by fetch_photos or pasted)")
    wiki_title = models.CharField(max_length=200, blank=True, help_text="Wikipedia article used for the photo")
    is_veg = models.BooleanField(default=True, verbose_name="Vegetarian")
    cook_time = models.PositiveIntegerField(help_text="Minutes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def ingredient_list(self):
        return [line.strip() for line in self.ingredients.splitlines() if line.strip()]

    def step_list(self):
        return [line.strip() for line in self.steps.splitlines() if line.strip()]

    def cuisine_info(self):
        return cuisine_info(self.cuisine)

    def photo_url(self):
        """Uploaded photo first, then the image link, else "" (templates show the letter placeholder)."""
        if self.image:
            return self.image.url
        return self.image_url or ""

    def photo_is_from_wikipedia(self):
        return not self.image and bool(self.wiki_title) and "wikimedia.org/" in self.image_url

    def wikipedia_url(self):
        return "https://en.wikipedia.org/wiki/" + quote(self.wiki_title.replace(" ", "_"))

    def short_ingredients(self, n=4):
        names = []
        for item in self.ingredient_list()[:n]:
            name = item.split(",")[0].split("(")[0]
            names.append(_QUANTITY.sub("", name).strip().lower())
        return ", ".join(names)

    def to_dict(self, request=None):
        """Used by the JSON API (AJAX search, Saved page and the AngularJS board)."""
        photo = self.photo_url()
        if photo.startswith("/") and request:
            photo = request.build_absolute_uri(photo)
        info = self.cuisine_info()
        return {
            "id": self.id,
            "title": self.title,
            "cuisine": info["name"],
            "cuisine_emoji": info["emoji"],
            "ingredients": self.ingredient_list(),
            "steps": self.step_list(),
            "image": photo,
            "is_veg": self.is_veg,
            "cook_time": self.cook_time,
        }


class Rating(models.Model):
    """A star rating. Uses the same `ratings` table as the CGI page and sql/ scripts."""
    name = models.CharField(max_length=60)
    recipe = models.CharField(max_length=120)
    stars = models.PositiveSmallIntegerField()
    comment = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ratings"
        managed = False   # table is created by migration 0002 (or sql/setup.sql)
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.recipe} ({self.stars})"
