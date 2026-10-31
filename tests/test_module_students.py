import pytest
from django.urls import reverse
from apps.accounts.models import User
from apps.core.laboratory import SYSTEM_MODELS
from apps.core.module_students import MODULE_STUDENTS

@pytest.mark.django_db
def test_student_profiles_on_every_module(client):
 u=User.objects.create_user(email='profile-test@example.test',password='DemoPass!742',full_name='QA',role='STUDENT',approval_status='ACTIVE')
 client.force_login(u)
 routes={m['route_name'] for models in SYSTEM_MODELS.values() for m in models}
 assert routes==set(MODULE_STUDENTS)
 for route in routes:
  r=client.get(reverse(route))
  assert r.status_code==200
  assert b'The student behind this module' in r.content
  if route == 'core:yankson':
   assert b'Portrait coming soon' not in r.content
   assert b'About the student' not in r.content
   assert b'module-student-portrait' not in r.content
   assert b'Emmanuel Yankson Sackey' in r.content
  else:
   assert b'Portrait coming soon' in r.content
   if route == 'core:p2_hybrid':
    assert b'torque-split dynamics' in r.content
   elif route == 'core:brakelab':
    assert b'Ebenezer Wilson' in r.content
    assert b'Hajime Shokai' in r.content
   elif route == 'core:wheel_slip':
    assert b'Abubakar Sadiq Ibrahim' in r.content
    assert b'Ghana Standards Authority' in r.content
    assert b'Meridian Port Services' in r.content
   else:
    assert b'A short student biography' in r.content
 assert b'The student behind this module' not in client.get(reverse('core:laboratory')).content
