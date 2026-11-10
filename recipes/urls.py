from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("recipe/<int:pk>/", views.detail, name="detail"),
    path("recipe/add/", views.add_recipe, name="add"),
    path("recipe/<int:pk>/edit/", views.edit_recipe, name="edit"),
    path("recipe/<int:pk>/delete/", views.delete_recipe, name="delete"),
    path("surprise/", views.surprise, name="surprise"),
    path("saved/", views.saved, name="saved"),
    path("browse/", views.browse, name="browse"),
    path("rate/", views.rate, name="rate"),
    # JSON endpoints
    path("api/recipes/", views.api_recipes, name="api_recipes"),
    path("api/search/", views.api_search, name="api_search"),
    path("export/", views.export_json, name="export"),
]
