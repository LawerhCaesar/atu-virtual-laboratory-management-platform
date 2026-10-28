import shutil
import subprocess
from pathlib import Path
import pytest
from django.urls import reverse
from apps.accounts.models import User


def test_engine_model_and_controller_contract():
    node=shutil.which('node')
    if not node:pytest.skip('Node required for engine model tests')
    result=subprocess.run([node,'--test',*[str(p) for p in sorted(Path('tests/engine').glob('*.test.mjs'))]],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr


def test_engine_page_requires_login(client):
    assert client.get(reverse('core:engine_live_data')).status_code==302


@pytest.mark.django_db
@pytest.mark.parametrize('role',['STUDENT','LECTURER','ADMIN'])
def test_engine_page_active_roles_and_views(client,role):
    user=User.objects.create_user(email=f'engine-{role}@example.test',full_name='Engine QA',password='SyntheticPass!742',role=role,approval_status='ACTIVE')
    client.force_login(user)
    for view in ['overview','fuel','idle','cooling','startRun','invalid']:
        response=client.get(reverse('core:engine_live_data'),{'view':view})
        assert response.status_code==200
        assert b'Engine Live Data Demonstration' in response.content
        assert b'data-module="core:engine_live_data"' in response.content
        assert b'data-initial-view="overview"' in response.content if view=='invalid' else True


@pytest.mark.django_db
def test_pending_student_cannot_open_engine_page(client):
    user=User.objects.create_user(email='engine-pending@example.test',full_name='Pending Engine QA',password='SyntheticPass!742')
    client.force_login(user)
    assert client.get(reverse('core:engine_live_data')).status_code==403
