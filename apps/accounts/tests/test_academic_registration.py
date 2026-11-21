import pytest
from django.urls import reverse
from apps.accounts.forms import RegistrationForm
from apps.accounts.models import User
from apps.accounts.services import approve_for_academic_setup
from apps.academics.catalogue import registration_catalogue
from apps.academics.forms import AcademicSetupForm
from apps.academics.models import AcademicProfile, Department, Faculty, Programme
from .test_registration_index import payload

pytestmark = pytest.mark.django_db


def test_verified_selection_persists_without_granting_or_creating_academic_access(client):
    response = client.post(reverse('accounts:register'), payload(programme='mtech-food-and-bioprocess-engineering'))
    assert response.status_code == 200
    user = User.objects.get(email='index@example.edu')
    assert user.registration_academics['department'] == 'Mechanical Engineering'
    assert user.registration_academics['programme'] == 'MTech Food and Bioprocess Engineering'
    assert user.registration_academics['catalogue_reviewed_on'] == '2026-11-21'
    assert user.approval_status == 'PENDING'
    assert not AcademicProfile.objects.filter(user=user).exists()
    assert not Faculty.objects.exists()
    administrator = User.objects.create_superuser('reviewer@example.edu', password='ReviewerPass!732', full_name='Reviewer')
    approve_for_academic_setup(user=user, reviewer=administrator)
    form = AcademicSetupForm(user=user)
    assert form.initial['department'] == Department.objects.get(name='Mechanical Engineering').pk
    assert form.initial['programme'] == Programme.objects.get(name='MTech Food and Bioprocess Engineering').pk
    assert user.approval_status == 'ACADEMIC_SETUP'
    assert not AcademicProfile.objects.filter(user=user).exists()
    html = client.get(reverse('accounts:register')).content.decode()
    assert 'registration-academic-catalogue' in html


@pytest.mark.parametrize('changes,field', [
    ({'faculty': ''}, 'faculty'), ({'department': ''}, 'department'),
    ({'programme': ''}, 'programme'), ({'department': 'computing'}, 'department'),
    ({'programme': 'hnd-automobile-engineering'}, 'programme'),
    ({'programme': 'btech-not-an-atu-programme'}, 'programme'),
    ({'programme': 'mtech-sustainable-electrical-power-engineering'}, 'programme'),
    ({'department': 'not-a-department'}, 'department'),
])
def test_server_rejects_missing_or_tampered_academic_combinations(changes, field):
    form = RegistrationForm(payload(**changes))
    assert not form.is_valid()
    assert field in form.errors


def test_unconfirmed_department_is_disclosed_and_not_promoted_to_an_assignment():
    form = RegistrationForm(payload(qualification='BTECH', index_number='01181429B', programme='btech-chemical-and-process-engineering'))
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.registration_academics['department_confirmation_required'] is True
    administrator = User.objects.create_superuser('reviewer@example.edu', password='ReviewerPass!732', full_name='Reviewer')
    approve_for_academic_setup(user=user, reviewer=administrator)
    assert 'programme' not in AcademicSetupForm(user=user).initial
    assert not Programme.objects.filter(name='BTech Chemical and Process Engineering').exists()
    assert not AcademicProfile.objects.filter(user=user).exists()


def test_lecturer_keeps_department_without_student_programme_or_index():
    form = RegistrationForm(payload(role='LECTURER', qualification='', index_number='', programme=''))
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.registration_academics['department_id'] == 'mechanical'
    assert user.registration_academics['programme_id'] == ''
    assert user.index_number is None


def test_catalogue_relationships_and_provenance_are_internally_consistent():
    data = registration_catalogue()
    faculties = {f['id'] for f in data['faculties']}
    departments = {d['id']: d for d in data['departments']}
    assert len(departments) == len(data['departments'])
    assert len({p['id'] for p in data['programmes']}) == len(data['programmes'])
    for department in departments.values():
        assert department['faculty'] in faculties
    for programme in data['programmes']:
        assert programme['qualification'] in {'HND', 'BTECH', 'MTECH'}
        assert all(source in data['sources'] for source in programme['sources'])
        if programme['department']:
            assert departments[programme['department']]['faculty'] == programme['faculty']
        else:
            assert programme['department_confirmed'] is False
    assert all(url.startswith('https://atu.edu.gh/') for url in data['sources'].values())
