import shutil
import subprocess
from pathlib import Path

import pytest
from django.urls import NoReverseMatch, reverse
from apps.accounts.models import User


def test_engine_model_and_controller_contract():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for browser-model contract tests.")
    files = sorted(str(path) for path in Path("tests/engine").glob("*.test.mjs"))
    result = subprocess.run([node, "--test", *files], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_withdrawn_engine_has_no_registered_route():
    with pytest.raises(NoReverseMatch):
        reverse("core:engine_live_data")


@pytest.mark.parametrize("view", ["overview", "fuel", "idle", "cooling", "startRun", "invalid"])
def test_withdrawn_engine_is_unavailable_to_guests(client, view):
    assert client.get("/virtual-lab/engine-live-data/", {"view": view}).status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["STUDENT", "LECTURER", "ADMIN"])
def test_withdrawn_engine_is_unavailable_to_active_roles(client, role):
    user = User.objects.create_user(email=f"engine-{role.lower()}@example.test", full_name="Engine QA", password="SyntheticPass!742", role=role,
                                    approval_status=User.ApprovalStatus.ACTIVE)
    client.force_login(user)
    for view in ["overview", "fuel", "idle", "cooling", "startRun", "invalid"]:
        assert client.get("/virtual-lab/engine-live-data/", {"view": view}).status_code == 404


@pytest.mark.django_db
def test_pending_student_cannot_open_engine_page(client):
    user = User.objects.create_user(email="engine-pending@example.test", full_name="Pending Engine QA", password="SyntheticPass!742")
    client.force_login(user)
    assert client.get("/virtual-lab/engine-live-data/").status_code == 404
