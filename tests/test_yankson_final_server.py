"""Supplementary server contract checks for the correction brief."""
import json
from unittest.mock import patch
import pytest
from django.test import Client
from apps.accounts.models import User
from apps.core.models import LabDeviceCredential
from test_starting_lab import post, BASE

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize('role', ['ADMIN', 'LECTURER', 'STUDENT'])
def test_ENV_01_approved_role_can_open_module(role):
    user = User.objects.create_user(email=role.lower()+'@example.test', password='TestOnly!392', role=role, approval_status='ACTIVE')
    client = Client()
    client.force_login(user)
    response = client.get('/virtual-lab/ice/authenticated-engine-starting/')
    assert response.status_code == 200
    assert b'ys-title' in response.content


def test_ID_03_challenge_origin_rp_and_uv_are_bound():
    user = User.objects.create_user(email='binding@example.test',password='TestOnly!392',approval_status='ACTIVE')
    client = Client()
    client.force_login(user)
    options = post(client,'device/register/options/').json()
    with patch('apps.core.starting_lab.verify_registration_response',side_effect=ValueError('invalid signature')) as verify:
        assert post(client,'device/register/complete/',{'verified':True}).status_code == 400
        args=verify.call_args.kwargs
        assert args['expected_origin'] == 'https://testserver'
        assert args['expected_rp_id'] == 'testserver'
        assert args['require_user_verification'] is True
        assert args['expected_challenge']
    assert not LabDeviceCredential.objects.exists()
    assert post(client,'device/register/complete/',{}).status_code == 400
    assert options['challenge']
