"""
Django settings for RecipeNest.

Database: MySQL by default. Change the values in DATABASES below to match
your own MySQL username and password.

Online (PythonAnywhere): put the live values in a .env file next to
manage.py (copy .env.example). Locally you don't need a .env file at all.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Read KEY=value lines from .env into os.environ (real environment variables win).
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _value = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _value.strip())

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"] + [
    host.strip() for host in os.environ.get("ALLOWED_HOSTS", "").split(",") if host.strip()
]
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host not in ("127.0.0.1", "localhost")]

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "recipes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "recipenest.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "recipes.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "recipenest.wsgi.application"

# Navbar links. Locally they open the Node.js and CGI servers; online (.env)
# set them to /browse/ and /rate/, the Django versions of the same pages.
QUICK_BROWSE_URL = os.environ.get("QUICK_BROWSE_URL", "http://localhost:3000")
RATE_URL = os.environ.get("RATE_URL", "http://localhost:8001/cgi-bin/rate.py")

# ---------------- DATABASE (MySQL) ----------------
# Set USE_SQLITE=1 only if you want to try the app without MySQL.
if os.environ.get("USE_SQLITE") == "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("MYSQL_DATABASE", "recipenest_db"),
            "USER": os.environ.get("MYSQL_USER", "root"),
            "PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
            "HOST": os.environ.get("MYSQL_HOST", "127.0.0.1"),
            "PORT": "3306",
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"   # `collectstatic` copies files here for the web server

# Uploaded recipe photos
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
