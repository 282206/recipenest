# RecipeNest

Live website: https://recipenest-3grn.onrender.com/

85 recipes from 14 cuisines with photos from Wikipedia. Search by ingredient, filter by cuisine
and veg / non-veg, save favourites, cook step by step in cook mode, and rate what you made.
Works on phones and in dark mode.

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

