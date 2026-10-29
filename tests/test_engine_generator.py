import subprocess
import pytest
from django.urls import reverse
from apps.accounts.models import User


def test_engine_generator_numerical_port():
    result=subprocess.run(['node','--test','tests/engine-generator/engine.test.mjs'],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr


def test_engine_generator_login_required(client):
    assert client.get(reverse('core:engine_generator')).status_code==302


@pytest.mark.django_db
@pytest.mark.parametrize('role',['ADMIN','LECTURER','STUDENT'])
def test_engine_generator_active_roles(client,role):
    u=User.objects.create_user(email=f'engine_generator-{role}@example.test',password='ExampleTest!74',full_name='QA',role=role,approval_status='ACTIVE')
    client.force_login(u)
    r=client.get(reverse('core:engine_generator'))
    assert r.status_code==200
    assert b'eg-app' in r.content and b'simulation-walkthrough' in r.content
    u.approval_status='PENDING';u.save()
    assert client.get(reverse('core:engine_generator')).status_code==403
