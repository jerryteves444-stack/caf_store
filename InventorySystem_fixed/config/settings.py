"""
Django settings for the Sales & inventory Management System.

Environment-driven so the same codebase runs against SQLite in development
and PostgreSQL in production. See .env.example for all supported variables.
"""
import os
import urllib.parse
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# Don't rely on VERCEL=1 alone - Vercel only guarantees that at build time
# unless "Automatically expose System Environment Variables" is turned on
# for the project, which isn't the default. VERCEL_URL and the Lambda
# runtime marker are both reliably present in the actual running function.
ON_VERCEL = bool(
    os.environ.get("VERCEL_URL")
    or os.environ.get("VERCEL") == "1"
    or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
)

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Core / security
# ---------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# Vercel terminates TLS at the edge and forwards requests over HTTP, so tell
# Django to trust the X-Forwarded-Proto header when deciding if a request is
# secure (needed for CSRF checks and SECURE_SSL_REDIRECT to behave correctly).
if ON_VERCEL:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
_vercel_url = os.environ.get("VERCEL_URL")
if _vercel_url:
    ALLOWED_HOSTS.append(_vercel_url)
    CSRF_TRUSTED_ORIGINS.append(f"https://{_vercel_url}")
_vercel_project_domain = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
if _vercel_project_domain:
    ALLOWED_HOSTS.append(_vercel_project_domain)
    CSRF_TRUSTED_ORIGINS.append(f"https://{_vercel_project_domain}")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]
THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "django_extensions" if config("USE_DJANGO_EXTENSIONS", default=False, cast=bool) else None,
]
THIRD_PARTY_APPS = [a for a in THIRD_PARTY_APPS if a]

LOCAL_APPS = [
    "core",
    "accounts",
    "dashboard",
    "inventory",
    "meat",
    "pricing",
    "sales",
    "customers",
    "suppliers",
    "purchases",
    "reports",
    "notifications",
    "audit",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "audit.middleware.AuditLogMiddleware",  # captures request.user / IP for signal-based logging
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.notifications_processor",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Vercel (and most managed Postgres providers - Neon, Supabase, Vercel Postgres)
# inject a single DATABASE_URL env var. Prefer that when present.
_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    _url = urllib.parse.urlparse(_database_url)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _url.path.lstrip("/"),
            "USER": _url.username,
            "PASSWORD": _url.password,
            "HOST": _url.hostname,
            "PORT": _url.port or "5432",
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"sslmode": "require"},
        }
    }
elif config("DB_ENGINE", default="sqlite") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME", default="store_system"),
            "USER": config("DB_USER", default="store_user"),
            "PASSWORD": config("DB_PASSWORD", default=""),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# Auth / passwords
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "accounts:login"

SESSION_COOKIE_AGE = config("SESSION_COOKIE_AGE", default=3600 * 8, cast=int)  # 8 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ---------------------------------------------------------------------------
# Security hardening (production values overridden via env)
# ---------------------------------------------------------------------------
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static / media
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
# Same reasoning as logging above: probe writability rather than trusting an
# env var that may not be present in the running function. Note this still
# doesn't make uploads persist on Vercel (/tmp is wiped between
# invocations) - it just prevents a crash. Wire up S3/Cloudinary via
# django-storages for real persistence.
_media_root = BASE_DIR / "media"
try:
    os.makedirs(_media_root, exist_ok=True)
    _probe = _media_root / ".write_test"
    with open(_probe, "w") as _f:
        _f.write("x")
    _probe.unlink()
    MEDIA_ROOT = _media_root
except OSError:
    MEDIA_ROOT = Path("/tmp/media")
    os.makedirs(MEDIA_ROOT, exist_ok=True)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Crispy forms
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ---------------------------------------------------------------------------
# Business rules (tweak per store policy)
# ---------------------------------------------------------------------------
LOW_STOCK_DEFAULT_THRESHOLD = config("LOW_STOCK_DEFAULT_THRESHOLD", default=10, cast=int)
EXPIRY_WARNING_DAYS = config("EXPIRY_WARNING_DAYS", default=7, cast=int)
DEFAULT_TAX_RATE = config("DEFAULT_TAX_RATE", default=0.12, cast=float)  # 12% VAT example
CURRENCY_SYMBOL = config("CURRENCY_SYMBOL", default="₱")

# ---------------------------------------------------------------------------
# Logging (errors -> file + console, when the filesystem allows it)
# ---------------------------------------------------------------------------
_log_handlers = ["console"]
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": _log_handlers, "level": "INFO", "propagate": False},
        "store_system": {"handlers": _log_handlers, "level": "DEBUG", "propagate": False},
    },
}
# Don't trust env-var platform detection here - serverless platforms don't
# always expose it to the running function the way they do at build time.
# Also don't trust os.access(W_OK) - a read-only *mount* (which is what
# Vercel actually uses) still reports writable permission bits, so
# os.access() lies here. The only reliable test is to actually write a byte
# and see if the filesystem rejects it.
try:
    os.makedirs(BASE_DIR / "logs", exist_ok=True)
    _probe = BASE_DIR / "logs" / ".write_test"
    with open(_probe, "w") as _f:
        _f.write("x")
    _probe.unlink()
    _logs_writable = True
except OSError:
    _logs_writable = False

if _logs_writable:
    LOGGING["handlers"]["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": BASE_DIR / "logs" / "app.log",
        "maxBytes": 5 * 1024 * 1024,
        "backupCount": 5,
        "formatter": "verbose",
    }
    _log_handlers.append("file")
