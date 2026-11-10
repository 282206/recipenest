from django.db import migrations, models

# The `ratings` table may already exist (sql/setup.sql or the CGI page create it),
# so create it only if it's missing, with SQL that matches setup.sql.
MYSQL_SQL = """
CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL,
    recipe VARCHAR(120) NOT NULL,
    stars TINYINT NOT NULL CHECK (stars BETWEEN 1 AND 5),
    comment VARCHAR(300),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SQLITE_SQL = """
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(60) NOT NULL,
    recipe VARCHAR(120) NOT NULL,
    stars SMALLINT NOT NULL CHECK (stars BETWEEN 1 AND 5),
    comment VARCHAR(300),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""


def create_ratings_table(apps, schema_editor):
    sql = MYSQL_SQL if schema_editor.connection.vendor == "mysql" else SQLITE_SQL
    schema_editor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Rating",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60)),
                ("recipe", models.CharField(max_length=120)),
                ("stars", models.PositiveSmallIntegerField()),
                ("comment", models.CharField(blank=True, max_length=300, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "ratings",
                "managed": False,
                "ordering": ["-created_at"],
            },
        ),
        migrations.RunPython(create_ratings_table, migrations.RunPython.noop),
    ]
