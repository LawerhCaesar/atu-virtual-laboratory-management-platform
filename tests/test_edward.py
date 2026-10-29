import subprocess
import pytest
from django.urls import reverse
from apps.accounts.models import User


def test_edward_numerical_port():
    result=subprocess.run(['node','-e',"const E=require('./static/js/edward/Edward_BEV_Virtual_Platform.js'); console.log(E.selfTest())"],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr


def test_edward_login_required(client):
    assert client.get(reverse('core:edward')).status_code==302


@pytest.mark.django_db
@pytest.mark.parametrize('role',['ADMIN','LECTURER','STUDENT'])
def test_edward_active_roles(client,role):
    u=User.objects.create_user(email=f'edward-{role}@example.test',password='ExampleTest!74',full_name='QA',role=role,approval_status='ACTIVE')
    client.force_login(u)
    r=client.get(reverse('core:edward'))
    assert r.status_code==200
    assert b'edward-lab' in r.content and b'simulation-walkthrough' in r.content
    u.approval_status='PENDING';u.save()
    assert client.get(reverse('core:edward')).status_code==403


def test_edward_reference_runtime_is_preserved():
    import hashlib
    from pathlib import Path
    source=Path('static/js/edward/Edward_BEV_Virtual_Platform.js').read_bytes()
    assert hashlib.sha256(source).hexdigest()=='217a9d22709e1c79d261acecd62f722c2edaa0f4234baa005bed567b78483b0d'
