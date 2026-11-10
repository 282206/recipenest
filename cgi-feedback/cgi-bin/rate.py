#!/usr/bin/env python3
"""
RecipeNest - "Rate a Recipe" page using Python CGI + MySQL Connector.

Run from the cgi-feedback folder:
    python -m http.server 8001 --cgi
Then open: http://localhost:8001/cgi-bin/rate.py

GET  -> shows the rating form (and ?recipe=Name pre-selects a recipe)
POST -> validates the form, INSERTs into MySQL, shows all ratings

Note: Python's old `cgi` module was removed in Python 3.13, so this script
reads the request by hand from environment variables and stdin.
"""
import html
import os
import sys
from urllib.parse import parse_qs

import mysql.connector

# Print UTF-8 (stars, curly quotes) correctly on Windows too
sys.stdout.reconfigure(encoding="utf-8")

# ---- change these to match your MySQL ----
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": "recipenest_db",
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ratings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(60) NOT NULL,
            recipe VARCHAR(120) NOT NULL,
            stars TINYINT NOT NULL CHECK (stars BETWEEN 1 AND 5),
            comment VARCHAR(300),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def read_request():
    """Return (method, fields) where fields is a dict of form values."""
    method = os.environ.get("REQUEST_METHOD", "GET").upper()
    if method == "POST":
        length = int(os.environ.get("CONTENT_LENGTH") or 0)
        body = sys.stdin.buffer.read(length).decode("utf-8") if length else ""
    else:
        body = os.environ.get("QUERY_STRING", "")
    parsed = parse_qs(body, keep_blank_values=True)
    fields = {key: values[0].strip() for key, values in parsed.items()}
    return method, fields


def recipe_titles(cur):
    try:
        cur.execute("SELECT title FROM recipes_recipe ORDER BY title")
        return [row[0] for row in cur.fetchall()]
    except mysql.connector.Error:
        return []  # Django tables not created yet


def all_ratings(cur):
    cur.execute("SELECT name, recipe, stars, comment, created_at FROM ratings ORDER BY created_at DESC")
    return cur.fetchall()


def validate(fields, titles):
    errors = []
    if len(fields.get("name", "")) < 2:
        errors.append("Enter your name (at least 2 characters).")
    if not fields.get("recipe"):
        errors.append("Choose a recipe.")
    elif titles and fields["recipe"] not in titles:
        errors.append("Choose a recipe from the list.")
    if fields.get("stars") not in {"1", "2", "3", "4", "5"}:
        errors.append("Pick a rating from 1 to 5 stars.")
    if len(fields.get("comment", "")) > 300:
        errors.append("Keep the comment under 300 characters.")
    return errors


# Same colours, fonts and dark mode as the Django site (recipes/static/recipes/css/style.css).
# Kept inside this file so the CGI page works even when Django isn't running.
STYLE = """
  :root {
    --bg: #FFFFFF; --surface: #FFFFFF; --steel: #EEF1EF; --ink: #1E2320; --muted: #5E6862; --line: #DCE2DE;
    --leaf: #2E5A3B; --leaf-hover: #22462D; --on-leaf: #FFFFFF; --heading: #2E5A3B;
    --turmeric: #E3A01B; --chili: #A8322A; --chili-soft: #F6DEDB; --danger: #B42318;
    color-scheme: light;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #141816; --surface: #1C211E; --steel: #262D29; --ink: #E8ECE9; --muted: #A3ADA7; --line: #333C37;
      --leaf: #7FB98E; --leaf-hover: #95C9A3; --on-leaf: #10160F; --heading: #A9D6B4;
      --turmeric: #F0B840; --chili: #EE8478; --chili-soft: #3A2421; --danger: #F38B80;
      color-scheme: dark;
    }
  }
  :root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
  body { font-family: "Figtree", system-ui, -apple-system, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); line-height: 1.55; }
  h1, h2, .wordmark { font-family: "Young Serif", Georgia, serif; font-weight: 400; }
  :focus-visible { outline: 3px solid var(--turmeric); outline-offset: 2px; }
  .wrap { max-width: 760px; }
  .top { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: .9rem 0; border-bottom: 1px solid var(--line); }
  .wordmark { font-size: 1.5rem; color: var(--heading); text-decoration: none; display: inline-flex; align-items: center; }
  .wordmark span { color: var(--turmeric); }
  .wordmark svg { width: 28px; height: 28px; margin-right: .45rem; }
  .back { color: var(--leaf); font-weight: 700; text-decoration: none; }
  .back:hover { text-decoration: underline; }
  .page-title { color: var(--heading); font-size: clamp(2rem, 4.5vw, 2.8rem); margin: 1.5rem 0 .4rem; }
  .section-title { font-size: 1.45rem; margin: 1.6rem 0 .6rem; }
  .sub, .hint { color: var(--muted); }
  .hint { font-weight: 400; font-size: .9rem; }
  .card-panel { background: var(--surface); border: 1px solid var(--line); border-radius: 22px; padding: clamp(1.25rem, 3vw, 2rem); }
  .form-label { font-weight: 700; }
  .form-control, .form-select { border-radius: 12px; background-color: var(--surface); color: var(--ink); border-color: var(--line); }
  .form-control:focus, .form-select:focus { border-color: var(--leaf); box-shadow: 0 0 0 3px rgba(46,90,59,.25); background-color: var(--surface); color: var(--ink); }
  .btn { border-radius: 12px; font-weight: 700; }
  .btn-leaf { background: var(--leaf); color: var(--on-leaf); border: 1px solid var(--leaf); }
  .btn-leaf:hover, .btn-leaf:focus { background: var(--leaf-hover); border-color: var(--leaf-hover); color: var(--on-leaf); }
  .star-pick { display: inline-flex; flex-direction: row-reverse; gap: .15rem; }
  .star-pick input { position: absolute; opacity: 0; width: 1px; height: 1px; }
  .star-pick label { font-size: 2.1rem; line-height: 1; color: var(--line); cursor: pointer; transition: transform .2s, color .2s; }
  .star-pick label:hover, .star-pick label:hover ~ label, .star-pick input:checked ~ label { color: var(--turmeric); }
  .star-pick label:hover { transform: scale(1.18); }
  .star-pick input:focus-visible + label { outline: 3px solid var(--turmeric); border-radius: 4px; }
  .table { --bs-table-bg: transparent; --bs-table-color: var(--ink); --bs-table-border-color: var(--line); }
  .table td.stars { color: var(--turmeric); letter-spacing: 1px; white-space: nowrap; }
  .alert-danger { background: var(--chili-soft); color: var(--ink); border-color: var(--chili); }
  .alert-success { background: var(--steel); color: var(--ink); border-color: var(--leaf); }
  @media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }
"""

LOGO = ('<svg viewBox="0 0 40 40" aria-hidden="true"><path d="M5 20h30a15 13 0 0 1-30 0z" style="fill:var(--leaf)"/>'
        '<rect x="3" y="17" width="34" height="5" rx="2.5" fill="#E3A01B"/>'
        '<path d="M15 13c-2-3 2-5 0-8M22 13c-2-3 2-5 0-8" stroke="#E3A01B" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg>')


def page(body):
    print("Content-Type: text/html; charset=utf-8")
    print()
    print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Rate a recipe | RecipeNest</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Cpath d='M5 20h30a15 13 0 0 1-30 0z' fill='%232E5A3B'/%3E%3Crect x='3' y='17' width='34' height='5' rx='2.5' fill='%23E3A01B'/%3E%3Cpath d='M15 13c-2-3 2-5 0-8M22 13c-2-3 2-5 0-8' stroke='%23E3A01B' stroke-width='2.4' fill='none' stroke-linecap='round'/%3E%3C/svg%3E">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&family=Young+Serif&display=swap" rel="stylesheet">
<style>{STYLE}</style>
</head>
<body>
<div class="container wrap pb-5">
  <header class="top">
    <a class="wordmark" href="http://127.0.0.1:8000/">{LOGO}Recipe<span>Nest</span></a>
    <a class="back" href="http://127.0.0.1:8000/">‹ Back to RecipeNest</a>
  </header>
  {body}
</div>
</body>
</html>""")


def form_html(titles, fields, errors):
    esc = html.escape
    options = "".join(
        f'<option value="{esc(t)}"{" selected" if t == fields.get("recipe") else ""}>{esc(t)}</option>'
        for t in titles
    )
    if titles:
        recipe_input = f'<select class="form-select" id="recipe" name="recipe"><option value="">Choose a recipe</option>{options}</select>'
    else:
        recipe_input = f'<input class="form-control" id="recipe" name="recipe" value="{esc(fields.get("recipe", ""))}">'

    # Star picker: listed 5 to 1 and flipped with CSS, so hovering lights up the stars before it
    star_radios = "".join(
        f'<input type="radio" name="stars" id="s{n}" value="{n}"'
        f'{" checked" if fields.get("stars") == str(n) else ""}>'
        f'<label for="s{n}" title="{n} star{"s" if n > 1 else ""}">★</label>'
        for n in range(5, 0, -1)
    )
    error_box = ""
    if errors:
        items = "".join(f"<li>{esc(e)}</li>" for e in errors)
        error_box = f'<div class="alert alert-danger"><ul class="mb-0">{items}</ul></div>'

    return f"""
  <h1 class="page-title">Rate a recipe</h1>
  <p class="sub mb-4">Cooked something from RecipeNest? Tell others how it turned out.</p>
  {error_box}
  <form method="post" action="/cgi-bin/rate.py" class="card-panel mb-5">
    <div class="mb-3">
      <label class="form-label" for="name">Your name</label>
      <input class="form-control" id="name" name="name" maxlength="60" value="{esc(fields.get('name', ''))}">
    </div>
    <div class="mb-3">
      <label class="form-label" for="recipe">Recipe</label>
      {recipe_input}
    </div>
    <fieldset class="mb-3">
      <legend class="form-label fs-6 mb-1">Rating</legend>
      <div class="star-pick">{star_radios}</div>
    </fieldset>
    <div class="mb-3">
      <label class="form-label" for="comment">Comment <span class="hint">optional</span></label>
      <textarea class="form-control" id="comment" name="comment" rows="3" maxlength="300">{esc(fields.get('comment', ''))}</textarea>
    </div>
    <button class="btn btn-leaf" type="submit">Submit rating</button>
  </form>"""


def ratings_html(rows):
    esc = html.escape
    if not rows:
        return '<h2 class="section-title">All ratings</h2><p>No ratings yet. Be the first to rate a recipe.</p>'
    body = "".join(
        f"<tr><td>{esc(name)}</td><td>{esc(recipe)}</td>"
        f"<td class='stars' aria-label='{stars} out of 5'>{'★' * stars}</td>"
        f"<td>{esc(comment or '')}</td><td class='text-nowrap'>{created:%d %b %Y}</td></tr>"
        for name, recipe, stars, comment, created in rows
    )
    return f"""
  <h2 class="section-title">All ratings</h2>
  <div class="table-responsive">
    <table class="table align-middle">
      <thead><tr><th>Name</th><th>Recipe</th><th>Rating</th><th>Comment</th><th>Date</th></tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>"""


def main():
    method, fields = read_request()
    try:
        conn = get_connection()
    except mysql.connector.Error as err:
        page(f'<div class="alert alert-danger mt-4">Couldn’t connect to MySQL: {html.escape(str(err))}. '
             f'Check DB_CONFIG at the top of rate.py.</div>')
        return

    cur = conn.cursor()
    ensure_table(cur)
    titles = recipe_titles(cur)
    notice = ""
    errors = []

    if method == "POST":
        errors = validate(fields, titles)
        if not errors:
            cur.execute(
                "INSERT INTO ratings (name, recipe, stars, comment) VALUES (%s, %s, %s, %s)",
                (fields["name"], fields["recipe"], int(fields["stars"]), fields.get("comment") or None),
            )
            conn.commit()
            notice = (f'<div class="alert alert-success mt-3">Thanks, {html.escape(fields["name"])}. '
                      f'Your rating for {html.escape(fields["recipe"])} is saved.</div>')
            fields = {}

    body = notice + form_html(titles, fields, errors) + ratings_html(all_ratings(cur))
    cur.close()
    conn.close()
    page(body)


main()
