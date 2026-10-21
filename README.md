# RecipeNest

A recipe book web app for the Web Technologies (AIM3140) project.
Add recipes with photos, search them by ingredient, filter veg and non-veg, and rate them.

Made by Gitika Gangwar.

## What's inside

```
RecipeNest/
├── manage.py
├── requirements.txt
├── recipenest/              Django project (settings, main urls)
├── recipes/                 Django app
│   ├── models.py            Recipe model
│   ├── views.py             pages + JSON API + JSON export
│   ├── forms.py             ModelForm for add/edit
│   ├── admin.py             Django Admin setup
│   ├── urls.py              URL routing
│   ├── templates/recipes/   HTML templates (Bootstrap)
│   ├── static/recipes/      style.css, validate.js, search.js
│   └── management/commands/load_recipes.py   loads seed JSON
├── seed/recipes.json        10 starter recipes
├── sql/                     setup.sql + crud_demo.sql for the MySQL command line
├── cgi-feedback/            "Rate a recipe" page (Python CGI + MySQL Connector)
└── node-board/              "Quick browse" page (Node.js + AngularJS)
```

## Syllabus coverage

| Topic | Where it is used |
|---|---|
| HTML, lists, tables, images, links, forms | All templates; add form has text, number, radio, textarea and file inputs; ratings table on the CGI page |
| CSS: inline, internal, external | `style="..."` in `detail.html`, `<style>` block in `base.html`, `static/recipes/css/style.css` |
| CSS box model, selectors, fonts, colors | `style.css` |
| Bootstrap grid, components, responsive design | Navbar, recipe card grid, alerts, form controls; works on mobile |
| JavaScript events, DOM, form validation | `validate.js` checks the add/edit form and previews the chosen photo |
| Python basics, CGI, GET and POST | `cgi-feedback/cgi-bin/rate.py` (GET shows the form, POST saves a rating) |
| MySQL CRUD on the command line | `sql/setup.sql`, `sql/crud_demo.sql` |
| Python DB connectivity with MySQL Connector | `rate.py` uses `mysql.connector` |
| JSON parsing in Python | `load_recipes` reads `seed/recipes.json`; Export JSON link writes JSON |
| jQuery + AJAX | `search.js`: live search calls `/api/search/?ing=...` without reloading |
| Node.js | `node-board/server.js` serves the page and forwards `/api/` calls to Django |
| AngularJS | `node-board/public/index.html`: `ng-repeat`, filters, sorting, `$http` |
| Django MVT, models, views, templates, admin, ORM, URL routing | `recipes/` app |

## Setup (one time)

You need Python 3.10 to 3.14, MySQL 8, and Node.js installed.

**1. Install Python packages**

```bash
cd RecipeNest
pip install -r requirements.txt
```

**2. Create the database in MySQL**

```bash
mysql -u root -p
```
```sql
SOURCE sql/setup.sql;
exit
```
(Use the full path to `setup.sql` if MySQL can't find it.)

**3. Put your MySQL password in two places**

- `recipenest/settings.py`: `"PASSWORD": ... "root"` → your password
- `cgi-feedback/cgi-bin/rate.py`: `DB_CONFIG["password"]` → your password

**4. Create Django tables, load starter recipes, make an admin user**

```bash
python manage.py migrate
python manage.py load_recipes
python manage.py createsuperuser
```

## Running it (3 terminals)

| Terminal | Command | Open |
|---|---|---|
| 1, Django (main site) | `python manage.py runserver` | http://127.0.0.1:8000 |
| 2, CGI ratings | `cd cgi-feedback` then `python -m http.server 8001 --cgi` | http://localhost:8001/cgi-bin/rate.py |
| 3, Node + AngularJS | `cd node-board` then `node server.js` | http://localhost:3000 |

The navbar links to all three, so once they're running you can move between them from the main site.

## 3-minute demo script

1. Home page: point out the Bootstrap grid and veg / non-veg marks.
2. Type "tomato" in the search box. Results change without a page reload (jQuery AJAX + Django JSON API).
3. Click **Add recipe** and submit it empty to show the JavaScript validation. Then fill it in with a photo and save.
4. Open **Admin** and show the recipe list, filter, and inline edit (Django Admin + ORM).
5. Open **Quick browse** and click Non-veg, then sort by quickest (Node.js + AngularJS).
6. Open **Rate a recipe**, submit a rating (CGI POST), and show it in the ratings table.
7. In the MySQL command line run `SELECT * FROM ratings;` and a few lines from `crud_demo.sql`.
8. Click **Export JSON** to download all recipes as JSON.

## Common problems

- **`Access denied for user 'root'`**: the password in `settings.py` or `rate.py` doesn't match your MySQL password.
- **`Unknown database 'recipenest_db'`**: run `sql/setup.sql` first (step 2).
- **Quick browse says it couldn't load recipes**: the Django server (terminal 1) isn't running.
- **CGI page downloads instead of running (Mac/Linux)**: run `chmod +x cgi-feedback/cgi-bin/rate.py`.
- **`--cgi` option not found**: Python 3.15 removed CGI support from `http.server`. Use Python 3.10 to 3.14 for that terminal.
- **Want to try it without MySQL?** Set `USE_SQLITE=1` before the Django commands (`set USE_SQLITE=1` on Windows CMD, `$env:USE_SQLITE=1` in PowerShell, `export USE_SQLITE=1` on Mac/Linux). The CGI page still needs MySQL.
