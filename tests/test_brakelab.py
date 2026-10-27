import shutil
import subprocess

import pytest
from django.urls import reverse

from apps.accounts.models import User


def test_brakelab_numerical_contract():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required to check the browser calculation contract")
    result = subprocess.run([node, "--test", "tests/brakelab/model.test.mjs"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_brakelab_route_requires_login(client):
    assert client.get(reverse("core:brakelab")).status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ADMIN", "LECTURER", "STUDENT"])
def test_active_roles_can_open_brakelab(client, role):
    user = User.objects.create_user(email=f"brake-{role}@example.test", full_name="Brake QA",
        password="SyntheticPass!742", role=role, approval_status=User.ApprovalStatus.ACTIVE)
    client.force_login(user)
    response = client.get(reverse("core:brakelab"))
    assert response.status_code == 200
    assert b"Regenerative and Friction Brake-Force Allocation" in response.content
    assert b"brakelab/ui.mjs" in response.content
    assert b"fuel-delivery/ui.mjs" not in response.content
    assert b"No hardware is connected" in response.content
    assert b"no Simulink-file or MATLAB runtime verification" in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("approval,is_active", [("PENDING", True), ("ACTIVE", False)])
def test_unapproved_or_inactive_users_cannot_open_brakelab(client, approval, is_active):
    user = User.objects.create_user(email="brake-blocked@example.test", full_name="Brake QA",
        password="SyntheticPass!742", approval_status=approval, is_active=is_active)
    client.force_login(user)
    assert client.get(reverse("core:brakelab")).status_code in (302, 403)
