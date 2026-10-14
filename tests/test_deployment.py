import io
import os
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from config.environment import env_bool, positive_int, validate_production_environment
from apps.accounts.models import User


def valid_environment():
    return {
        "DJANGO_SECRET_KEY": "test-only-random-style-secret-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "DJANGO_ALLOWED_HOSTS": "lab.example.edu",
        "POSTGRES_HOST": "db",
        "POSTGRES_DB": "atu_test",
        "POSTGRES_USER": "atu_test",
        "POSTGRES_PASSWORD": "test-only-not-a-real-deployment-password",
    }


def test_explicit_production_configuration_is_accepted():
    validate_production_environment(valid_environment())


@pytest.mark.parametrize("name", ["DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"])
def test_missing_production_configuration_fails_closed(name):
    environment = valid_environment()
    environment.pop(name)
    with pytest.raises(ImproperlyConfigured):
        validate_production_environment(environment)


@pytest.mark.parametrize("hosts", ["*", ".example.edu", "https://lab.example.edu", "lab.example.edu,*"])
def test_production_wildcard_and_url_hosts_are_rejected(hosts):
    environment = valid_environment()
    environment["DJANGO_ALLOWED_HOSTS"] = hosts
    with pytest.raises(ImproperlyConfigured):
        validate_production_environment(environment)


@pytest.mark.parametrize("value", ["0", "-1", "invalid"])
def test_limit_configuration_requires_positive_values(value):
    with pytest.raises(ImproperlyConfigured):
        positive_int({"LIMIT": value}, "LIMIT", 300)


def test_boolean_configuration_rejects_typographical_errors():
    with pytest.raises(ImproperlyConfigured):
        env_bool({"FLAG": "flase"}, "FLAG")


@pytest.mark.django_db
def test_database_readiness_probe_is_read_only():
    output = io.StringIO()
    call_command("check_database", stdout=output)
    assert output.getvalue().strip() == "Database ready."


@pytest.mark.django_db
def test_postgresql_probe_rejects_sqlite():
    from django.db import connection
    if connection.vendor != "sqlite":
        pytest.skip("SQLite-only fallback assertion.")
    with pytest.raises(CommandError, match="PostgreSQL is required"):
        call_command("check_database", require_postgresql=True)


@pytest.mark.django_db
def test_private_responses_cannot_be_cached(client):
    user = User.objects.create_superuser(email="secure-test@example.edu", full_name="Secure Test", password="StrongPass!742")
    client.force_login(user)
    for name in ("core:dashboard", "accounts:user_management", "reporting:users_csv"):
        response = client.get(reverse(name))
        assert response.status_code == 200
        assert "no-store" in response["Cache-Control"]
        assert response["X-Content-Type-Options"] == "nosniff"


def test_public_recovery_pages_cannot_be_cached(client):
    response = client.get(reverse("accounts:login"))
    assert "no-store" in response["Cache-Control"]


def test_csrf_is_required_for_public_registration():
    from django.test import Client
    assert Client(enforce_csrf_checks=True).post(reverse("accounts:register"), {}).status_code == 403


def test_trusted_proxy_https_configuration_and_host_rejection(client, settings):
    settings.SECURE_SSL_REDIRECT = True
    settings.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    settings.ALLOWED_HOSTS = ["lab.example.edu"]
    assert client.get("/", HTTP_HOST="lab.example.edu").status_code == 301
    assert client.get("/", HTTP_HOST="lab.example.edu", HTTP_X_FORWARDED_PROTO="https").status_code == 200
    assert client.get("/", HTTP_HOST="untrusted.example.edu", HTTP_X_FORWARDED_PROTO="https").status_code == 400


@pytest.mark.django_db
def test_media_has_no_public_application_route(client):
    assert client.get("/media/evidence/test.txt").status_code == 404


def test_private_storage_permissions(settings, tmp_path):
    from django.core.files.storage import FileSystemStorage
    storage = FileSystemStorage(location=tmp_path)
    name = storage.save("nested/protected.txt", SimpleUploadedFile("protected.txt", b"Educational fixture"))
    assert os.stat(storage.path(name)).st_mode & 0o777 == 0o600
    assert os.stat(tmp_path / "nested").st_mode & 0o777 == 0o700


@pytest.mark.django_db
def test_recovery_check_detects_missing_evidence(settings, tmp_path):
    from apps.practicals.models import EvidenceFile
    settings.DEBUG = True
    settings.MEDIA_ROOT = tmp_path
    call_command("seed_demo_data", stdout=io.StringIO())
    output = io.StringIO()
    call_command("verify_evidence_storage", stdout=output)
    assert "1 references, 0 missing" in output.getvalue()
    # Change only a test DB reference, without deleting a file.
    EvidenceFile.objects.update(file="missing-fixture.txt")
    with pytest.raises(CommandError, match="1 missing of 1"):
        call_command("verify_evidence_storage")


def test_production_configuration_keeps_bootstrap_credentials_private():
    import yaml
    configuration = yaml.safe_load(Path("compose.production.yaml").read_text())
    web = configuration["services"]["web"]
    assert not web.get("ports")
    assert "POSTGRES_ADMIN_PASSWORD" not in str(web["environment"])
    assert "POSTGRES_ADMIN_PASSWORD" not in str(configuration["services"]["migrate"]["environment"])
    assert "POSTGRES_ADMIN_PASSWORD" in str(configuration["services"]["db"]["environment"])
    assert configuration["networks"]["backend"]["internal"] is True
    assert configuration["services"]["db"]["volumes"][0].endswith(":/var/lib/postgresql")
    assert "--require-least-privilege" in web["healthcheck"]["test"]


def test_ci_defines_disposable_postgresql_and_browser_verification():
    import yaml
    workflow = yaml.safe_load(Path(".github/workflows/verify.yaml").read_text())
    assert workflow["on"] == ["push", "pull_request"]
    job = workflow["jobs"]["postgres-and-browser"]
    assert job["services"]["postgres"]["image"] == "postgres:18-alpine"
    assert any("pytest -m e2e" in step.get("run", "") for step in job["steps"])


@pytest.mark.django_db
def test_administrator_bootstrap_validates_password_and_does_not_print_it():
    with pytest.raises(CommandError):
        call_command("bootstrap_admin", email="bootstrap-test@example.edu", full_name="Bootstrap Test", password="123", no_input=True, stdout=io.StringIO())
    assert not User.objects.filter(email="bootstrap-test@example.edu").exists()
    output = io.StringIO()
    secret = "SyntheticBootstrap!842"
    call_command("bootstrap_admin", email="bootstrap-test@example.edu", full_name="Bootstrap Test", password=secret, no_input=True, stdout=output)
    assert secret not in output.getvalue()
    assert User.objects.get(email="bootstrap-test@example.edu").must_change_password
