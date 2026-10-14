import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.academics.models import AcademicProfile, Department, Faculty, Programme


pytestmark = pytest.mark.django_db


def test_academic_profile_rejects_mismatched_hierarchy():
    engineering = Faculty.objects.create(name="Engineering", code="ENG")
    science = Faculty.objects.create(name="Science", code="SCI")
    automotive = Department.objects.create(faculty=engineering, name="Automotive", code="AUTO")
    computing = Department.objects.create(faculty=science, name="Computing", code="COMP")
    programme = Programme.objects.create(department=computing, name="Computing MSc", code="MSC-COMP")
    student = User.objects.create_user(
        email="hierarchy@example.edu",
        full_name="Hierarchy Student",
        role=User.Role.STUDENT,
        password="SafePassword!238",
    )
    profile = AcademicProfile(
        user=student,
        faculty=engineering,
        department=automotive,
        programme=programme,
        student_or_staff_id="ID-001",
    )

    with pytest.raises(ValidationError):
        profile.full_clean()

