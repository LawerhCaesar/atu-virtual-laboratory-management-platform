import pytest
from django.urls import reverse

from apps.accounts.models import User


def test_reference_welcome_keeps_real_account_routes(client):
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert b"MTech Automotive Engineering" in response.content
    assert b"atu-crest.png" in response.content
    assert b'href="/accounts/register/"' in response.content
    assert b'href="/accounts/login/"' in response.content
    assert b"Your approved account determines your role" in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ADMIN", "LECTURER", "STUDENT"])
def test_every_dashboard_exposes_installed_engine(client, role):
    user = User.objects.create_user(
        email=f"shell-{role.lower()}@example.test", full_name="UI QA",
        password="SyntheticPass!742", role=role,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    client.force_login(user)
    response = client.get(reverse("core:dashboard"))
    assert response.status_code == 200
    assert b"Open engine simulations" in response.content
    assert reverse("core:engine_live_data").encode() in response.content
    assert b"No physical hardware is connected" in response.content
    assert b"Return to your dashboard" in client.get(reverse("core:home")).content
