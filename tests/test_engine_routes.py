import shutil
import subprocess
from pathlib import Path

import pytest
from django.urls import reverse
from apps.accounts.models import User


def test_engine_model_and_controller_contract():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for browser-model contract tests.")
    files = sorted(str(path) for path in Path("tests/engine").glob("*.test.mjs"))
    result = subprocess.run([node, "--test", *files], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_engine_requires_authentication(client):
    response = client.get(reverse("core:engine_live_data"))
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["STUDENT", "LECTURER", "ADMIN"])
def test_active_academic_roles_can_open_engine_page(client, role):
    user = User.objects.create_user(email=f"engine-{role.lower()}@example.test", full_name="Engine QA", password="SyntheticPass!742", role=role,
                                    approval_status=User.ApprovalStatus.ACTIVE)
    client.force_login(user)
    response = client.get(reverse("core:engine_live_data"))
    assert response.status_code == 200
    assert b"Engine Live-Data Demonstration" in response.content
    assert b"physical 1NZ setup has no electric water pump" in response.content


@pytest.mark.django_db
def test_pending_student_cannot_open_engine_page(client):
    user = User.objects.create_user(email="engine-pending@example.test", full_name="Pending Engine QA", password="SyntheticPass!742")
    client.force_login(user)
    assert client.get(reverse("core:engine_live_data")).status_code == 403
