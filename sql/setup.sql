-- =====================================================
-- RecipeNest - MySQL setup
-- Run in the MySQL command line:
--   mysql -u root -p
--   SOURCE path/to/sql/setup.sql;
-- =====================================================

CREATE DATABASE IF NOT EXISTS recipenest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE recipenest_db;

-- Ratings table, used by the CGI "Rate a recipe" page.
-- (Django creates its own recipes_recipe table when you run migrate.)
CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL,
    recipe VARCHAR(120) NOT NULL,
    stars TINYINT NOT NULL CHECK (stars BETWEEN 1 AND 5),
    comment VARCHAR(300),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SHOW TABLES;
