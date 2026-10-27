import shutil
import subprocess

import pytest
from django.urls import reverse

from apps.accounts.models import User


def test_wheel_slip_numerical_contract():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the simulation tests")
    result = subprocess.run([node, "--test", "tests/wheel_slip/model.test.mjs"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_wheel_slip_requires_sign_in(client):
    assert client.get(reverse("core:wheel_slip")).status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ADMIN", "LECTURER", "STUDENT"])
def test_active_roles_can_access_wheel_slip(client, role):
    user = User.objects.create_user(email=f"ws-{role}@example.test", full_name="Wheel QA",
        password="SyntheticPass!742", role=role, approval_status=User.ApprovalStatus.ACTIVE)
    client.force_login(user)
    response = client.get(reverse("core:wheel_slip"))
    assert response.status_code == 200
    assert b"Wheel-Slip Control Using ABS and TCS" in response.content
    assert b"source Simulink file has not been inspected" in response.content


@pytest.mark.django_db
def test_pending_user_cannot_access_wheel_slip(client):
    user = User.objects.create_user(email="ws-pending@example.test", full_name="Pending",
        password="SyntheticPass!742", approval_status=User.ApprovalStatus.PENDING)
    client.force_login(user)
    assert client.get(reverse("core:wheel_slip")).status_code in (302, 403)
