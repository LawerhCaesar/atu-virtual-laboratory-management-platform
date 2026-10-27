import shutil
import subprocess

import pytest
from django.urls import reverse
from apps.accounts.models import User

def test_steering_numerical_contract():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for numerical checks')
    result = subprocess.run([node, '--test', 'tests/steering_response/model.test.mjs'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

def test_steering_requires_sign_in(client):
    assert client.get(reverse('core:steering_response')).status_code == 302

@pytest.mark.django_db
@pytest.mark.parametrize('role', ['ADMIN','LECTURER','STUDENT'])
def test_steering_active_role_access(client, role):
    user=User.objects.create_user(email=f'steering-{role}@example.test',full_name='Steering QA',password='SyntheticPass!742',role=role,approval_status=User.ApprovalStatus.ACTIVE)
    client.force_login(user)
    response=client.get(reverse('core:steering_response'))
    assert response.status_code == 200
    assert b'Vehicle Steering Response' in response.content
    assert b'core:steering_response' in response.content
    assert b'1,500 kg base mass' in response.content

@pytest.mark.django_db
def test_steering_blocks_unapproved_account(client):
    user=User.objects.create_user(email='steering-pending@example.test',full_name='Pending QA',password='SyntheticPass!742',approval_status=User.ApprovalStatus.PENDING)
    client.force_login(user)
    assert client.get(reverse('core:steering_response')).status_code in (302,403)
