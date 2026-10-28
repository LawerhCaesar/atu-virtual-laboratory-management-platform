import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.core.laboratory import ICE_MODELS, BEV_MODELS, SYSTEMS


def test_home_lists_all_five_systems(client):
    content = client.get(reverse("core:home")).content.decode()
    assert "Engine Live Data Demonstration" not in content
    assert "/virtual-lab/engine-live-data/" not in content
    for system in SYSTEMS:
        assert f'<dt>{system["code"]}</dt>' in content
        assert system["name"] in content


@pytest.mark.parametrize("path", ["/virtual-lab/", "/virtual-lab/systems/fcev/"])
def test_laboratory_requires_login(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ADMIN", "LECTURER", "STUDENT"])
def test_system_catalogues_are_scoped_to_system(client, role):
    user = User.objects.create_user(email=f"lab-{role.lower()}@example.test", full_name="Lab QA",
        password="SyntheticPass!742", role=role, approval_status=User.ApprovalStatus.ACTIVE)
    client.force_login(user)
    dashboard = client.get(reverse("core:dashboard"))
    assert dashboard.status_code == 200
    assert b"Engine Live Data Demonstration" not in dashboard.content
    assert b"/virtual-lab/engine-live-data/" not in dashboard.content
    response = client.get(reverse("core:laboratory"))
    assert response.status_code == 200
    assert b"Engine Live Data Demonstration" not in response.content
    assert b"/virtual-lab/engine-live-data/" not in response.content
    for system in SYSTEMS:
        url = reverse("core:laboratory_system", args=[system["slug"]])
        assert url.encode() in response.content
        environment = client.get(url)
        assert environment.status_code == 200
        assert system["name"].encode() in environment.content
        if system["slug"] != "ice":
            assert b"Engine Live Data Demonstration" not in environment.content
            assert b"/virtual-lab/engine-live-data/" not in environment.content
        if system["slug"] == "ice":
            assert len(ICE_MODELS) == 2
            for model in ICE_MODELS:
                assert model["title"].encode() in environment.content
                assert reverse(model["route_name"]).encode() in environment.content
            assert b"?view=" not in environment.content
            assert b"4 learning models" not in response.content
            assert b"2 simulation models available" in response.content
        elif system["slug"] == "bev":
            assert len(BEV_MODELS) == 1
            assert b"Regenerative and Friction Brake-Force Allocation" in environment.content
            assert reverse("core:brakelab").encode() in environment.content
            assert reverse("core:fuel_delivery").encode() not in environment.content
        elif system["slug"] == "vehicle-dynamics":
            assert b"Wheel-Slip Control Using ABS and TCS" in environment.content
            assert reverse("core:wheel_slip").encode() in environment.content
            assert b"Vehicle Steering Response" in environment.content
            assert reverse("core:steering_response").encode() in environment.content
            assert reverse("core:fuel_delivery").encode() not in environment.content
        elif system["slug"] == "hybrid":
            assert b"P2 Full-Parallel Hybrid" in environment.content
            assert reverse("core:p2_hybrid").encode() in environment.content
            assert b"12 V Micro-Hybrid Stop-Start" in environment.content
            assert reverse("core:micro_hybrid").encode() in environment.content
            assert reverse("core:fuel_delivery").encode() not in environment.content
        elif system["slug"] == "fcev":
            assert reverse("core:bless").encode() in environment.content
            assert b"Fuel-Cell / Battery and Diesel Comparison" in environment.content
        else:
            assert b"No simulations added yet" in environment.content
            assert b"Scope for future models" not in environment.content
            assert b"lab-model-grid" not in environment.content
            assert b"lab-launch" not in environment.content
            for placeholder in [b"Battery behaviour", b"Fuel-cell stack", b"Hydrogen supply", b"Power split", b"Regenerative braking", b"Longitudinal motion", b"Ride and suspension"]:
                assert placeholder not in environment.content
            assert reverse("core:fuel_delivery").encode() not in environment.content
    assert client.get(reverse("core:laboratory_system", args=["unknown"])).status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("approval,is_active", [("PENDING", True), ("ACTIVE", False)])
def test_unapproved_or_inactive_users_cannot_enter_laboratory(client, approval, is_active):
    user = User.objects.create_user(email="lab-blocked@example.test", full_name="Lab QA",
        password="SyntheticPass!742", approval_status=approval, is_active=is_active)
    client.force_login(user)
    for path in ["/virtual-lab/", *[f'/virtual-lab/systems/{s["slug"]}/' for s in SYSTEMS]]:
        assert client.get(path).status_code in (302, 403)
