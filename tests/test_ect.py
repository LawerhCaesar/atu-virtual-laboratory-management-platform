import subprocess
import pytest
from django.urls import reverse
from apps.accounts.models import User


def test_ect_numerical_port():
    result=subprocess.run(['node','static/js/ect/Amachie_ECT_Virtual_Platform.js','--self-test'],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr


def test_ect_login_required(client):
    assert client.get(reverse('core:ect')).status_code==302


@pytest.mark.django_db
@pytest.mark.parametrize('role',['ADMIN','LECTURER','STUDENT'])
def test_ect_active_roles(client,role):
    u=User.objects.create_user(email=f'ect-{role}@example.test',password='ExampleTest!74',full_name='QA',role=role,approval_status='ACTIVE')
    client.force_login(u)
    r=client.get(reverse('core:ect'))
    assert r.status_code==200
    assert b'ect-lab' in r.content and b'simulation-walkthrough' in r.content
    u.approval_status='PENDING';u.save()
    assert client.get(reverse('core:ect')).status_code==403


def test_ect_reference_runtime_is_preserved():
    import hashlib
    from pathlib import Path
    source=Path('static/js/ect/Amachie_ECT_Virtual_Platform.js').read_bytes()
    assert hashlib.sha256(source).hexdigest()=='72daeb446e8eac9b14ba408e7bcbe6fb4bc473489942547a55e294db9c9e42cc'
