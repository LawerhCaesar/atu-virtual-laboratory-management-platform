import shutil
import subprocess
from pathlib import Path

import pytest
from django.urls import reverse

from apps.accounts.models import User


def test_fuel_numerical_contract():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required to check the browser calculation contract")
    result = subprocess.run([node, "--test", *map(str, Path("tests/fuel_delivery").glob("*.test.mjs"))], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_fuel_route_requires_login(client):
    assert client.get(reverse("core:fuel_delivery")).status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ADMIN", "LECTURER", "STUDENT"])
def test_active_roles_can_open_fuel_delivery(client, role):
    user = User.objects.create_user(email=f"fuel-{role}@example.test", full_name="Fuel QA", password="SyntheticPass!742",
        role=role, approval_status=User.ApprovalStatus.ACTIVE)
    client.force_login(user)
    response = client.get(reverse("core:fuel_delivery"))
    assert response.status_code == 200
    assert b"Fuel Delivery Optimisation" in response.content
    assert b"fuel-delivery/ui.mjs" in response.content
    assert b"engine-live-data/ui.mjs" not in response.content
    assert b"No hardware is connected" in response.content


@pytest.mark.django_db
def test_pending_user_cannot_open_fuel_delivery(client):
    user = User.objects.create_user(email="fuel-pending@example.test", full_name="Pending", password="SyntheticPass!742")
    client.force_login(user)
    assert client.get(reverse("core:fuel_delivery")).status_code == 403
