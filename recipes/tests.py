"""RecipeNest tests. Run with:  python manage.py test recipes
(set USE_SQLITE=1 first if MySQL is not running). One test also needs Node.js."""
import io
import json
import re
import shutil
import subprocess
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from recipes.management.commands import fetch_photos
from recipes.models import Rating, Recipe

MEDIA = tempfile.mkdtemp()


def png(size=(10, 10), fmt="PNG", name="p.png", ctype="image/png"):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=ctype)


def cards_in(html):
    return html.count('class="rcard card-in"')


@override_settings(MEDIA_ROOT=MEDIA)
class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_recipes", stdout=io.StringIO())
        # fake photos so photo features are testable without the network
        for r in Recipe.objects.exclude(title="Sweet and Sour Chicken"):
            r.image_url = f"https://upload.wikimedia.org/wikipedia/commons/x/{r.pk}.jpg"
            r.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)


class Seed(Base):
    def test_counts(self):
        self.assertEqual(Recipe.objects.count(), 85)
        self.assertEqual(Recipe.objects.values("cuisine").distinct().count(), 14)
        self.assertFalse(Recipe.objects.get(title="Egg Curry").is_veg)
        self.assertFalse(Recipe.objects.get(title="Fluffy Pancakes").is_veg)

    def test_rerun_updates_without_duplicates(self):
        poha = Recipe.objects.get(title="Poha")
        poha.cuisine, poha.wiki_title = "Other", ""
        poha.save()
        out = io.StringIO()
        call_command("load_recipes", stdout=out)
        self.assertIn("0 new recipes and updated 1", out.getvalue())
        poha.refresh_from_db()
        self.assertEqual((poha.cuisine, poha.wiki_title), ("Indian", "Indori Poha"))
        self.assertEqual(Recipe.objects.count(), 85)

    def test_photo_url_order(self):
        r = Recipe.objects.get(title="Poha")
        self.assertTrue(r.photo_url().startswith("https://upload.wikimedia.org"))
        self.assertTrue(r.photo_is_from_wikipedia())
        r.image = png()
        r.save()
        self.assertTrue(r.photo_url().startswith("/media/recipes/"))
        self.assertFalse(r.photo_is_from_wikipedia())
        self.assertEqual(Recipe.objects.get(title="Sweet and Sour Chicken").photo_url(), "")


class FetchPhotos(Base):
    def test_batches_redirects_and_skips(self):
        Recipe.objects.update(image_url="")
        uploaded = Recipe.objects.get(title="Poha")
        uploaded.image = png()
        uploaded.save()
        calls = []

        def fake_urlopen(request, timeout):
            calls.append(request)
            self.assertIn("RecipeNest", request.get_header("User-agent"))
            titles = re.search(r"titles=([^&]+)", request.full_url).group(1)
            titles = [t for t in __import__("urllib.parse").parse.unquote_plus(titles).split("|")]
            self.assertLessEqual(len(titles), 40)
            pages, normalized, redirects = {}, [], []
            for i, t in enumerate(titles):
                if t == "Paneer makhani":   # normalized + redirected
                    normalized.append({"from": t, "to": "Paneer Makhani"})
                    redirects.append({"from": "Paneer Makhani", "to": "Butter paneer"})
                    pages[str(i)] = {"title": "Butter paneer", "thumbnail": {"source": "https://upload.wikimedia.org/bp.jpg"}}
                elif t == "Pad thai":       # article without a picture
                    pages[str(i)] = {"title": t}
                else:
                    pages[str(i)] = {"title": t, "thumbnail": {"source": f"https://upload.wikimedia.org/{i}.jpg"}}
            body = json.dumps({"query": {"normalized": normalized, "redirects": redirects, "pages": pages}}).encode()
            return io.BytesIO(body)

        out = io.StringIO()
        with mock.patch.object(fetch_photos.urllib.request, "urlopen", fake_urlopen):
            call_command("fetch_photos", stdout=out)
        self.assertEqual(len(calls), 3)          # 84 titles -> 40 + 40 + 4
        self.assertEqual(Recipe.objects.get(title="Paneer Butter Masala").image_url, "https://upload.wikimedia.org/bp.jpg")
        self.assertEqual(Recipe.objects.get(title="Pad Thai").image_url, "")
        self.assertEqual(Recipe.objects.get(title="Poha").image_url, "")   # has an uploaded photo
        self.assertIn("Saved Wikipedia photos for 83 of 84", out.getvalue())
        self.assertIn("No photo found for: Pad Thai", out.getvalue())


class Home(Base):
    def test_default(self):
        html = self.client.get("/").content.decode()
        self.assertIn("<strong>85</strong> recipes from <strong>14</strong> cuisines", html)
        self.assertEqual(html.count('class="hero-photo'), 3)
        self.assertIn("Today’s pick", html)
        self.assertIn('id="featured" >', html.replace('id="featured"  >', 'id="featured" >'))
        self.assertEqual(html.count('class="cuisine-tile"'), 15)            # All + 14
        self.assertIn('href="/?cuisine=Italian#all-recipes"', html)
        self.assertIn('85 recipes</p>', html)
        self.assertIn('href="/?page=2#all-recipes"', html)
        grid = html.split('id="recipe-grid"')[1]
        self.assertEqual(cards_in(grid), 24)
        # first 14 cards: one per cuisine (Recommended = round robin)
        cuisines = re.findall(r'class="chip-cuisine">\S+ ([^<]+)<', grid)[:14]
        self.assertEqual(len(set(cuisines)), 14)
        quick = html.split("Ready in 20 minutes")[1].split('id="all-recipes"')[0]
        self.assertEqual(cards_in(quick), 12)
        self.assertEqual(html.count('loading="lazy"') >= 24, True)
        self.assertIn('onerror="rnPhotoFail(this)"', html)

    def test_filters(self):
        r = self.client.get("/?cuisine=Italian")
        html = r.content.decode()
        self.assertIn("Italian recipes", html)
        self.assertIn("12 recipes", html)
        self.assertIn('id="featured" hidden', html)
        self.assertIn('class="active-filter"', html)
        self.assertIn('aria-current="true">\n        <span class="cuisine-icon" style="--tint:#F9DCD5"', html)
        grid = html.split('id="recipe-grid"')[1]
        self.assertEqual(set(re.findall(r'class="chip-cuisine">\S+ ([^<]+)<', grid)), {"Italian"})

        html = self.client.get("/?type=veg&sort=quick").content.decode()
        grid = html.split('id="recipe-grid"')[1]
        self.assertNotIn('aria-label="Non-veg"', grid)
        times = [int(t) for t in re.findall(r"</svg>(\d+) min</span>", grid)]
        self.assertEqual(times, sorted(times))

        html = self.client.get("/?sort=az").content.decode()
        titles = re.findall(r'class="rcard-link"[^>]*><span[^>]*></span>([^<]+)</a>', html.split('id="recipe-grid"')[1])
        self.assertEqual(titles, sorted(titles))

    def test_pagination(self):
        html = self.client.get("/?page=4").content.decode()
        self.assertEqual(cards_in(html.split('id="recipe-grid"')[1]), 85 - 72)
        self.assertIn('id="show-more" href="" hidden', html)
        self.assertIn("Page 4 of 4", html)

    def test_search_and_empty(self):
        html = self.client.get("/?q=tomato").content.decode()
        self.assertIn("Search results", html)
        self.assertIn("for “tomato”", html)
        html = self.client.get("/?q=zzzz").content.decode()
        self.assertIn("No recipes match “zzzz” with these filters.", html)

    def test_surprise(self):
        r = self.client.get("/surprise/")
        self.assertRegex(r["Location"], r"^/recipe/\d+/$")


class Api(Base):
    def test_search_matches_home(self):
        d = self.client.get("/api/search/", {"ing": "rice", "type": "nonveg", "sort": "quick"}).json()
        html = self.client.get("/?q=rice&type=nonveg&sort=quick").content.decode()
        grid = html.split('id="recipe-grid"')[1]
        server_titles = re.findall(r'class="rcard-link"[^>]*><span[^>]*></span>([^<]+)</a>', grid)
        self.assertEqual([r["title"] for r in d["recipes"]][:24], [t.replace("&#x27;", "'") for t in server_titles])
        self.assertEqual(d["label"], f"{d['count']} non-veg recipes for “rice”")
        first = d["recipes"][0]
        for key in ["cuisine", "cuisine_emoji", "image", "ingredients", "steps", "is_veg", "cook_time"]:
            self.assertIn(key, first)

    def test_ids(self):
        a, b = Recipe.objects.order_by("id")[:2]
        d = self.client.get("/api/recipes/", {"ids": f"{b.id},{a.id},99999,abc,{b.id}"}).json()
        self.assertEqual([r["id"] for r in d["recipes"]], [b.id, a.id])

    def test_uploaded_photo_is_absolute(self):
        r = Recipe.objects.get(title="Poha")
        r.image = png()
        r.save()
        d = self.client.get("/api/recipes/", {"ids": r.id}).json()
        self.assertTrue(d["recipes"][0]["image"].startswith("http://testserver/media/recipes/"))

    def test_export(self):
        data = json.loads(self.client.get("/export/").content)
        self.assertEqual(len(data), 85)
        self.assertEqual(set(data[0]), {"title", "is_veg", "cook_time", "cuisine", "wiki_title", "image_url", "ingredients", "steps"})

    def test_js_card_matches_django_card(self):
        """cards.js must produce the same card as _card.html."""
        r = Recipe.objects.get(title="Chicken Tacos")
        api = self.client.get("/api/recipes/", {"ids": r.id}).json()["recipes"][0]
        html = self.client.get("/?q=Chicken+Tacos").content.decode()
        server = re.search(r'<article class="rcard card-in".*?</article>', html.split('id="recipe-grid"')[1], re.S).group(0)
        js = subprocess.run(["node", "-e", f"""
            global.window = {{}}; require('{__file__.rsplit('/', 1)[0]}/static/recipes/js/cards.js');
            process.stdout.write(window.RN.cardHtml({json.dumps(api)}, 0));"""],
            capture_output=True, text=True, check=True).stdout
        norm = lambda s: re.sub(r">\s+<", "><", re.sub(r"\s+", " ", s)).replace("&#x27;", "&#39;").strip()
        self.assertEqual(norm(js), norm(server))


class Detail(Base):
    def test_page(self):
        r = Recipe.objects.get(title="Margherita Pizza")
        Rating.objects.create(name="A", recipe=r.title, stars=5)
        Rating.objects.create(name="B", recipe=r.title, stars=4)
        html = self.client.get(f"/recipe/{r.pk}/").content.decode()
        self.assertIn('href="/?cuisine=Italian#all-recipes">Italian</a>', html)
        self.assertIn("4.5 from 2 ratings", html)
        self.assertIn('Photo from <a href="https://en.wikipedia.org/wiki/Pizza_Margherita"', html)
        self.assertIn(f'href="http://localhost:8001/cgi-bin/rate.py?recipe=Margherita%20Pizza"', html)
        self.assertIn("More Italian recipes", html)
        more = html.split("More Italian recipes")[1]
        self.assertEqual(cards_in(more), 4)
        self.assertIn('id="delete-form" method="post"', html)
        self.assertEqual(html.count('class="ing-item"'), len(r.ingredient_list()))

    def test_fill_when_few(self):
        r = Recipe.objects.get(cuisine="Greek")
        html = self.client.get(f"/recipe/{r.pk}/").content.decode()
        self.assertIn("More recipes to try", html)
        self.assertEqual(cards_in(html.split("More recipes to try")[1]), 4)

    def test_no_rating_no_photo(self):
        r = Recipe.objects.get(title="Sweet and Sour Chicken")
        html = self.client.get(f"/recipe/{r.pk}/").content.decode()
        self.assertNotIn("from 1 rating", html)
        self.assertIn('detail-photo placeholder-photo nonveg', html)
        self.assertNotIn("Photo from", html)


class Forms(Base):
    def data(self, **extra):
        return {"title": "Test Dal", "is_veg": "True", "cuisine": "Thai", "cook_time": "25",
                "ingredients": "dal\nsalt", "steps": "boil", "image_url": "", **extra}

    def test_add_with_link(self):
        r = self.client.post("/recipe/add/", self.data(image_url="https://example.com/a.jpg"))
        rec = Recipe.objects.get(title="Test Dal")
        self.assertRedirects(r, f"/recipe/{rec.pk}/", fetch_redirect_response=False)
        self.assertEqual((rec.cuisine, rec.image_url), ("Thai", "https://example.com/a.jpg"))

    def test_errors_match_js(self):
        cases = {
            "image_url": ("http://example.com/a.jpg", "Paste a full image link that starts with https://"),
            "cook_time": ("0", "Enter the cooking time in whole minutes, between 1 and 600."),
            "ingredients": ("only one", "Add at least 2 ingredients, one per line."),
            "title": ("Hi", "Enter a recipe name of at least 3 characters."),
        }
        for field, (value, message) in cases.items():
            r = self.client.post("/recipe/add/", self.data(**{field: value}))
            self.assertContains(r, message, msg_prefix=field)
        r = self.client.post("/recipe/add/", self.data(cook_time="601"))
        self.assertContains(r, "between 1 and 600")
        r = self.client.post("/recipe/add/", self.data(title="poha"))
        self.assertContains(r, "A recipe with this name already exists")
        r = self.client.post("/recipe/add/", self.data(steps=""))
        self.assertContains(r, "Add at least one step.")
        self.assertFalse(Recipe.objects.filter(title="Test Dal").exists())

    def test_upload_checks(self):
        r = self.client.post("/recipe/add/", self.data(image=png(fmt="GIF", name="a.gif", ctype="image/gif")))
        self.assertContains(r, "Choose a JPG or PNG photo.")
        big = SimpleUploadedFile("big.png", png().read() + b"0" * (5 * 1024 * 1024), content_type="image/png")
        r = self.client.post("/recipe/add/", self.data(image=big))
        self.assertContains(r, "smaller than 5 MB")
        r = self.client.post("/recipe/add/", self.data(image=png()))
        self.assertEqual(r.status_code, 302)

    def test_edit_keeps_and_clears_photo(self):
        self.client.post("/recipe/add/", self.data(image=png()))
        rec = Recipe.objects.get(title="Test Dal")
        self.assertContains(self.client.get(f"/recipe/{rec.pk}/edit/"), 'name="image-clear"')
        self.client.post(f"/recipe/{rec.pk}/edit/", self.data(cuisine="Korean"))
        rec.refresh_from_db()
        self.assertTrue(rec.image)
        self.assertEqual(rec.cuisine, "Korean")
        self.client.post(f"/recipe/{rec.pk}/edit/", self.data(**{"image-clear": "on"}))
        rec.refresh_from_db()
        self.assertFalse(rec.image)

    def test_delete(self):
        rec = Recipe.objects.get(title="Poha")
        self.client.post(f"/recipe/{rec.pk}/delete/")
        self.assertFalse(Recipe.objects.filter(pk=rec.pk).exists())


class Other(Base):
    def test_admin(self):
        User.objects.create_superuser("a", "a@a.com", "pw")
        self.client.login(username="a", password="pw")
        r = self.client.get("/admin/recipes/recipe/?cuisine__exact=Thai")
        self.assertContains(r, "4 recipes")
        self.assertContains(self.client.get("/admin/recipes/recipe/?q=Korean"), "3 recipes")

    def test_rate_page(self):
        r = self.client.post("/rate/", {"name": "Gitika", "recipe": "Poha", "stars": "5"}, follow=True)
        self.assertContains(r, "Your rating for Poha is saved")
        self.assertContains(r, 'class="star-pick"')

    def test_css_types_present(self):
        html = self.client.get("/").content.decode()
        self.assertIn('<link rel="stylesheet" href="/static/recipes/css/style.css">', html)
        self.assertIn("<style>", html)
        self.assertIn('style="fill:var(--leaf)"', html)

    @override_settings(QUICK_BROWSE_URL="/browse/", RATE_URL="/rate/")
    def test_online_links(self):
        html = self.client.get("/").content.decode()
        self.assertIn('href="/browse/"', html)
        self.assertIn('href="/rate/"', html)
        self.assertNotIn("localhost:3000", html)
