from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = "RecipeNest Admin"
admin.site.site_title = "RecipeNest Admin"
admin.site.index_title = "Manage recipes"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Pages without our <link rel="icon"> (like Django Admin) still ask for /favicon.ico
    path("favicon.ico", RedirectView.as_view(url=static_url("recipes/favicon.svg"), permanent=True)),
    path("", include("recipes.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
