import json
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .environment import env_bool, positive_int, postgres_options, validate_production_environment


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "development-only-change-before-deployment")
DEBUG = env_bool(os.environ, "DJANGO_DEBUG", True)
if not DEBUG:
    validate_production_environment(os.environ)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts",
    "apps.academics",
    "apps.auditlog",
    "apps.core",
    "apps.practicals",
    "apps.reporting",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.PrivateResponseMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "apps.accounts.middleware.SessionIdleTimeoutMiddleware",
    "apps.accounts.middleware.ForcePasswordChangeMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.notification_summary",
                "apps.core.context_processors.simulation_walkthrough",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if os.getenv("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "atu_virtual_lab"),
            "USER": os.getenv("POSTGRES_USER", "atu_virtual_lab"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": postgres_options(os.environ),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Accra"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.getenv("DJANGO_MEDIA_ROOT", str(BASE_DIR / "media")))
FILE_UPLOAD_PERMISSIONS = 0o600
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o700

EVIDENCE_FILE_MAX_BYTES = positive_int(os.environ, "EVIDENCE_FILE_MAX_BYTES", 20 * 1024 * 1024)
EVIDENCE_SUBMISSION_MAX_BYTES = positive_int(os.environ, "EVIDENCE_SUBMISSION_MAX_BYTES", 100 * 1024 * 1024)
EVIDENCE_ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".csv", ".txt"}
EVIDENCE_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/csv",
    "text/plain",
    "application/vnd.ms-excel",
}

try:
    INTEGRATION_SHARED_SECRETS = json.loads(os.getenv("INTEGRATION_SHARED_SECRETS", "{}"))
except json.JSONDecodeError as exc:
    raise ValueError("INTEGRATION_SHARED_SECRETS must be a JSON object.") from exc
if not isinstance(INTEGRATION_SHARED_SECRETS, dict):
    raise ValueError("INTEGRATION_SHARED_SECRETS must be a JSON object.")
if any(not isinstance(value, str) or not value for value in INTEGRATION_SHARED_SECRETS.values()):
    raise ImproperlyConfigured("Integration shared secrets must be non-empty strings.")
if not DEBUG and any(len(value) < 32 or value.startswith("replace-") for value in INTEGRATION_SHARED_SECRETS.values()):
    raise ImproperlyConfigured("Production integration shared secrets must be strong, non-placeholder values.")
INTEGRATION_RETURN_TOKEN_MAX_AGE_SECONDS = positive_int(os.environ, "INTEGRATION_RETURN_TOKEN_MAX_AGE_SECONDS", 1800)
INTEGRATION_CALLBACK_MAX_BYTES = positive_int(os.environ, "INTEGRATION_CALLBACK_MAX_BYTES", 1024 * 1024)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "core:home"

SESSION_COOKIE_AGE = positive_int(os.environ, "SESSION_IDLE_TIMEOUT_SECONDS", 300)
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
if not DEBUG and any(not origin.startswith("https://") or "*" in origin for origin in CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured("Production CSRF trusted origins must be explicit HTTPS origins.")
# Enable only behind the private proxy that overwrites this header.
if env_bool(os.environ, "DJANGO_TRUST_PROXY_HEADERS"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(os.environ, "DJANGO_HSTS_INCLUDE_SUBDOMAINS")
    SECURE_HSTS_PRELOAD = env_bool(os.environ, "DJANGO_HSTS_PRELOAD")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
