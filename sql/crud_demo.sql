-- =====================================================
-- RecipeNest - CRUD demo for the MySQL command line
-- Run these one by one AFTER `python manage.py migrate`
-- and `python manage.py load_recipes`. Take screenshots for the report.
-- =====================================================
USE recipenest_db;

-- See the table Django created
DESCRIBE recipes_recipe;

-- CREATE
INSERT INTO ratings (name, recipe, stars, comment)
VALUES ('Gitika', 'Poha', 5, 'Perfect quick breakfast');

INSERT INTO ratings (name, recipe, stars, comment)
VALUES ('Aman', 'Chole', 4, 'Needed a little more spice');

-- READ
SELECT id, title, cook_time, is_veg FROM recipes_recipe;
SELECT title, cook_time FROM recipes_recipe WHERE is_veg = 1 ORDER BY cook_time;
SELECT title FROM recipes_recipe WHERE ingredients LIKE '%paneer%';
SELECT cuisine, COUNT(*) AS recipes FROM recipes_recipe GROUP BY cuisine ORDER BY recipes DESC;
SELECT title, cook_time FROM recipes_recipe WHERE cuisine = 'Italian' AND cook_time <= 30;
SELECT recipe, ROUND(AVG(stars), 1) AS avg_stars, COUNT(*) AS total
FROM ratings GROUP BY recipe;

-- UPDATE
UPDATE recipes_recipe SET cook_time = 20 WHERE title = 'Poha';
UPDATE ratings SET stars = 5 WHERE name = 'Aman';

-- DELETE
DELETE FROM ratings WHERE name = 'Aman';

SELECT * FROM ratings;
