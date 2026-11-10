from django.contrib import admin

from .models import Rating, Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "cuisine", "is_veg", "cook_time", "created_at")
    list_filter = ("cuisine", "is_veg")
    search_fields = ("title", "cuisine", "ingredients")
    list_editable = ("is_veg", "cook_time")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("recipe", "name", "stars", "created_at")
    list_filter = ("stars",)
    search_fields = ("recipe", "name", "comment")
