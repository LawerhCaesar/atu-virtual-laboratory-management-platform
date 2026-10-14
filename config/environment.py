"""Fail-closed parsing for deployment configuration (without database access)."""
from django.core.exceptions import ImproperlyConfigured


def env_bool(environ, name, default=False):
    value = str(environ.get(name, str(default))).lower()
    if value not in {"true", "false", "1", "0", "yes", "no"}:
        raise ImproperlyConfigured(f"{name} must be a boolean.")
    return value in {"true", "1", "yes"}


def positive_int(environ, name, default):
    try:
        value = int(environ.get(name, default))
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(f"{name} must be a positive integer.") from exc
    if value <= 0:
        raise ImproperlyConfigured(f"{name} must be a positive integer.")
    return value


def validate_production_environment(environ):
    secret = environ.get("DJANGO_SECRET_KEY", "")
    if len(secret) < 50 or len(set(secret)) < 5 or any(
        marker in secret.lower() for marker in ("replace-", "development-only", "change-before")
    ):
        raise ImproperlyConfigured("Production requires a strong, explicit DJANGO_SECRET_KEY.")
    hosts = [host.strip() for host in environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if host.strip()]
    if not hosts or any("*" in host or host.startswith(".") or "://" in host for host in hosts):
        raise ImproperlyConfigured("Production requires explicit, non-wildcard DJANGO_ALLOWED_HOSTS.")
    for name in ("POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"):
        value = environ.get(name, "")
        if not value or value.startswith("replace-") or value == "local-development-password":
            raise ImproperlyConfigured(f"Production requires an explicit {name}.")
