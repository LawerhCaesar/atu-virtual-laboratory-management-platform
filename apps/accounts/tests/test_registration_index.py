import pytest
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import IntegrityError, DataError, transaction
from django.urls import reverse
from unittest.mock import patch
from apps.accounts.forms import RegistrationForm
from apps.accounts.models import User
from apps.academics.forms import AcademicSetupForm
from apps.academics.models import AcademicProfile,Faculty,Department,Programme

pytestmark=pytest.mark.django_db

def payload(**changes):
    data=dict(full_name='Index Student',email='index@example.edu',role='STUDENT',qualification='MTECH',index_number='01181429M',password1='SafeExample!482',password2='SafeExample!482')
    data.update(changes);return data

@pytest.mark.parametrize('course,suffix',[('HND','D'),('BTECH','B'),('MTECH','M')])
def test_course_index_saved_and_pending_login_not_bypassed(client,course,suffix):
    response=client.post(reverse('accounts:register'),payload(qualification=course,index_number='01181429'+suffix.lower()))
    assert response.status_code==200
    user=User.objects.get(email='index@example.edu')
    assert user.index_number=='01181429'+suffix and user.qualification==course
    assert user.approval_status=='PENDING' and user.check_password('SafeExample!482')
    assert client.post(reverse('accounts:login'),{'username':user.index_number,'password':'SafeExample!482'}).status_code==200
    assert '_auth_user_id' not in client.session
    user.approval_status='ACTIVE';user.save()
    assert authenticate(username=user.index_number.lower(),password='SafeExample!482')==user
    assert authenticate(username='INDEX@EXAMPLE.EDU',password='SafeExample!482')==user
    response=client.post(reverse('accounts:login'),{'username':user.index_number,'password':'SafeExample!482'})
    assert response.status_code==302

@pytest.mark.parametrize('value',['0118142M','011814299M','A1181429M','٠١١٨١٤٢٩M','01181429B','01181429D','0118 429M','01181429!',''])
def test_bad_index_rejected_even_without_browser_rules(value):
    form=RegistrationForm(payload(index_number=value));assert not form.is_valid();assert 'index_number' in form.errors

def test_course_required_and_duplicate_index_rejected(client):
    assert not RegistrationForm(payload(qualification='')).is_valid()
    client.post(reverse('accounts:register'),payload())
    form=RegistrationForm(payload(email='other@example.edu',index_number='01181429m'))
    assert not form.is_valid();assert 'index_number' in form.errors
    form=RegistrationForm(payload(email='INDEX@EXAMPLE.EDU',index_number='11181429M'))
    assert not form.is_valid();assert 'email' in form.errors

def test_lecturers_and_legacy_accounts_keep_email_access(client):
    form=RegistrationForm(payload(role='LECTURER',qualification='',index_number=''))
    assert form.is_valid(),form.errors
    lecturer=form.save();assert lecturer.index_number is None and lecturer.qualification==''
    legacy=User.objects.create_user('legacy@example.edu',password='LegacySafe!492',full_name='Legacy',approval_status='ACTIVE')
    assert authenticate(username='LEGACY@EXAMPLE.EDU',password='LegacySafe!492')==legacy

def test_password_cannot_equal_the_new_index_username():
    form=RegistrationForm(payload(password1='01181429M',password2='01181429M'))
    assert not form.is_valid();assert 'password2' in form.errors

@pytest.mark.parametrize('changes',[{'index_number':'01181429D','qualification':'MTECH'},{'index_number':'01181429M\n','qualification':'MTECH'},{'index_number':None,'qualification':'MTECH'},{'index_number':'01181429M','qualification':'MTECH','role':'LECTURER'}])
def test_database_rejects_invalid_paired_identity(changes):
    user=User.objects.create_user('db-rule@example.edu',full_name='QA')
    with pytest.raises((IntegrityError, DataError)),transaction.atomic():User.objects.filter(pk=user.pk).update(**changes)

def test_approval_setup_prefills_and_preserves_registered_index():
    student=User.objects.create_user('setup@example.edu',full_name='QA',index_number='01181429M',qualification='MTECH',role='STUDENT')
    faculty=Faculty.objects.create(name='Engineering',code='ENG');department=Department.objects.create(name='Auto',code='AUTO',faculty=faculty);programme=Programme.objects.create(name='MTech Automotive',code='MTECH',department=department)
    assert AcademicSetupForm(user=student).initial['student_or_staff_id']==student.index_number
    data=dict(faculty=faculty.pk,department=department.pk,programme=programme.pk,student_or_staff_id='wrong')
    form=AcademicSetupForm(data,user=student);assert not form.is_valid();assert 'student_or_staff_id' in form.errors
    profile=AcademicProfile(user=student,faculty=faculty,department=department,programme=programme,student_or_staff_id='wrong')
    with pytest.raises(ValidationError):profile.full_clean()
    data['student_or_staff_id']='01181429m';assert AcademicSetupForm(data,user=student).is_valid()
    profile.student_or_staff_id='01181429M';profile.save()
    applicant=RegistrationForm(payload(email='new@example.edu'))
    assert not applicant.is_valid();assert 'index_number' in applicant.errors

def test_duplicate_race_is_a_form_error_not_a_server_failure(client):
    with patch('apps.accounts.forms.RegistrationForm.save',side_effect=IntegrityError('duplicate')):
        response=client.post(reverse('accounts:register'),payload())
    assert response.status_code==200 and b'already uses that email address or index number' in response.content
    assert not User.objects.filter(email='index@example.edu').exists()
