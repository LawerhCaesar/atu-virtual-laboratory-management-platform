import base64
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError
from django.urls import reverse
import yaml

from config.environment import postgres_options, render_signing_key, validate_production_environment


def test_supabase_options_require_ssl_and_isolate_schema():
    assert postgres_options({"POSTGRES_SSLMODE": "require", "POSTGRES_SCHEMA": "atu_staging"}) == {
        "sslmode": "require", "options": "-c search_path=atu_staging", "connect_timeout": 5,
    }


@pytest.mark.parametrize("schema", ["public,atu_staging", "atu staging", "x;drop table users", "A"])
def test_postgres_schema_rejects_unsafe_search_paths(schema):
    with pytest.raises(ImproperlyConfigured):
        postgres_options({"POSTGRES_SCHEMA": schema})


@pytest.mark.django_db
def test_readiness_checks_database_without_login(client):
    response = client.get(reverse("core:readiness"))
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert "no-store" in response["Cache-Control"]


def test_readiness_hides_database_failure_details(client):
    with patch("apps.core.views.connection.cursor", side_effect=OperationalError("private database details")):
        response = client.get(reverse("core:readiness"))
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert b"private database details" not in response.content


@pytest.mark.parametrize("secret", [
    "synthetic-render-test-key-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    base64.b64encode(bytes(range(32))).decode(),
])
def test_render_profile_requires_production_security_and_exact_host(secret):
    environment = {k: v for k, v in os.environ.items() if not k.startswith(("DJANGO_", "POSTGRES_", "RENDER_"))}
    environment.update(
        DJANGO_SECRET_KEY=secret,
        DJANGO_DEBUG="true",
        RENDER_EXTERNAL_HOSTNAME="atu-qa.onrender.com",
        POSTGRES_HOST="example.invalid", POSTGRES_USER="test", POSTGRES_DB="test",
        POSTGRES_PASSWORD="synthetic-test-password", POSTGRES_SCHEMA="atu_staging",
    )
    code = """
import json, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.render_settings'
import django
django.setup()
from django.conf import settings
from django.test import Client
print(json.dumps({
    'debug': settings.DEBUG, 'hosts': settings.ALLOWED_HOSTS,
    'origins': settings.CSRF_TRUSTED_ORIGINS,
    'ssl': settings.DATABASES['default']['OPTIONS']['sslmode'],
    'cookie': settings.SESSION_COOKIE_SECURE,
    'redirect': Client().get('/accounts/login/', HTTP_HOST='atu-qa.onrender.com').status_code,
}))
"""
    result = subprocess.run([sys.executable, "-c", code], env=environment, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == {
        "debug": False, "hosts": ["atu-qa.onrender.com"],
        "origins": ["https://atu-qa.onrender.com"], "ssl": "require",
        "cookie": True, "redirect": 301,
    }


def test_render_generated_key_derivation_is_stable_and_preserves_validation():
    generated = base64.b64encode(bytes(range(32))).decode()
    assert len(render_signing_key(generated)) == 128
    assert render_signing_key(generated) == render_signing_key(generated)
    for weak in ("", "short", base64.b64encode(b"x" * 32).decode()):
        with pytest.raises(ImproperlyConfigured):
            validate_production_environment({"DJANGO_SECRET_KEY": render_signing_key(weak)})


def test_render_blueprint_keeps_password_out_of_source_and_uploads_on_disk():
    service = yaml.safe_load(Path("render.yaml").read_text())["services"][0]
    variables = {variable["key"]: variable for variable in service["envVars"]}
    assert variables["POSTGRES_PASSWORD"] == {"key": "POSTGRES_PASSWORD", "sync": False}
    assert variables["DJANGO_SECRET_KEY"]["generateValue"] is True
    assert variables["DJANGO_MEDIA_ROOT"]["value"].startswith(service["disk"]["mountPath"] + "/")
    assert service["autoDeployTrigger"] == "off"
    assert service["healthCheckPath"] == "/health/ready/"


def test_static_build_permissions_do_not_inherit_private_upload_modes(tmp_path):
    environment = os.environ.copy()
    environment["DJANGO_DEBUG"] = "true"
    environment["DJANGO_SETTINGS_MODULE"] = "config.build_settings"
    code = """
import os, sys
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
settings.STATIC_ROOT = sys.argv[1]
call_command('collectstatic', interactive=False, verbosity=0)
assert os.stat(settings.STATIC_ROOT).st_mode & 0o777 == 0o755
assert os.stat(os.path.join(settings.STATIC_ROOT, 'vendor/bootstrap/bootstrap.min.css')).st_mode & 0o777 == 0o644
"""
    subprocess.run([sys.executable, "-c", code, str(tmp_path / "static")],
                   env=environment, capture_output=True, text=True, check=True)
