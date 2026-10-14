"""Render staging profile; use config.settings for other deployment targets."""
import os
import re

from django.core.exceptions import ImproperlyConfigured

from .environment import render_signing_key

hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.onrender\.com", hostname):
    raise ImproperlyConfigured("Render must provide its exact external hostname.")

os.environ["DJANGO_DEBUG"] = "false"
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", hostname)
os.environ.setdefault("DJANGO_CSRF_TRUSTED_ORIGINS", f"https://{hostname}")
os.environ["DJANGO_TRUST_PROXY_HEADERS"] = "true"
os.environ["POSTGRES_SSLMODE"] = "require"
os.environ["DJANGO_SECRET_KEY"] = render_signing_key(os.environ.get("DJANGO_SECRET_KEY", ""))

from .settings import *  # noqa: E402,F403

# The internal health probe must query the database instead of returning an
# HTTPS redirect. All ordinary application routes still require HTTPS.
SECURE_REDIRECT_EXEMPT = [r"^health/ready/$"]
