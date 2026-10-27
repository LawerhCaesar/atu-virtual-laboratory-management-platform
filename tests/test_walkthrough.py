from types import SimpleNamespace
import shutil
import subprocess

from django.urls import reverse
import pytest

from apps.accounts.models import User
from apps.core.context_processors import simulation_walkthrough


def test_guide_content_contract():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required to check guide content")
    result = subprocess.run([node, "--test", "tests/walkthrough/steps.test.mjs"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.django_db
@pytest.mark.parametrize("route", ["core:fuel_delivery", "core:brakelab", "core:wheel_slip", "core:micro_hybrid"])
def test_active_module_renders_reusable_guide(client, route):
    user = User.objects.create_user(email=f"{route.replace(':', '-')}@example.test", full_name="Tutorial QA",
        password="SyntheticPass!742", role=User.Role.STUDENT, approval_status=User.ApprovalStatus.ACTIVE)
    client.force_login(user)
    response = client.get(reverse(route))
    assert response.status_code == 200
    assert b'id="simulation-walkthrough"' in response.content
    assert f'data-module="{route}"'.encode() in response.content
    assert b'js/walkthrough/ui.mjs' in response.content
    assert b'data-user="' + str(user.pk).encode() + b'"' in response.content
    assert b'Genesis GV70' in response.content
    assert b'0.371 m wheel radius' in response.content
    if route in ("core:brakelab", "core:wheel_slip"):
        assert b'1,500 kg vehicle mass and 0.31 m wheel radius' in response.content


def test_catalogue_registration_automatically_enables_future_module(monkeypatch):
    from apps.core import laboratory

    monkeypatch.setattr(laboratory, "SYSTEM_MODELS", {"future": ({"title": "Future lab", "route_name": "future:module"},)})
    user = SimpleNamespace(is_authenticated=True, is_platform_active=True, pk=42)
    request = SimpleNamespace(user=user, resolver_match=SimpleNamespace(view_name="future:module"))
    assert simulation_walkthrough(request)["walkthrough_module"] == {"route": "future:module", "name": "Future lab", "user_id": "42"}
    request.resolver_match.view_name = "core:dashboard"
    assert simulation_walkthrough(request) == {}
    request.user.is_platform_active = False
    request.resolver_match.view_name = "future:module"
    assert simulation_walkthrough(request) == {}
