import time

import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.academics.models import AcademicProfile, Department, Faculty, Programme
from apps.auditlog.models import AuditEvent


pytestmark = pytest.mark.django_db


@pytest.fixture
def administrator():
    return User.objects.create_superuser(
        email="admin@example.edu",
        full_name="Platform Administrator",
        password="StrongPass!742",
    )


@pytest.fixture
def academic_structure():
    faculty = Faculty.objects.create(name="Faculty of Engineering", code="ENG")
    department = Department.objects.create(
        faculty=faculty,
        name="Automotive Engineering Department",
        code="AUTO",
    )
    programme = Programme.objects.create(
        department=department,
        name="MTech Automotive Engineering",
        code="MTECH-AUTO",
    )
    return faculty, department, programme


def registration_payload(**overrides):
    data = {
        "full_name": "Ama Mensah",
        "email": "ama@example.edu",
        "role": User.Role.STUDENT,
        "password1": "SafePassword!238",
        "password2": "SafePassword!238",
    }
    data.update(overrides)
    return data


def test_public_registration_creates_pending_account_and_audit_event(client):
    response = client.post(reverse("accounts:register"), registration_payload())

    assert response.status_code == 200
    user = User.objects.get(email="ama@example.edu")
    assert user.role == User.Role.STUDENT
    assert user.approval_status == User.ApprovalStatus.PENDING
    assert not user.is_staff
    assert AuditEvent.objects.filter(action="ACCOUNT_REGISTERED", actor=user).exists()


def test_public_registration_rejects_administrator_role(client):
    response = client.post(
        reverse("accounts:register"),
        registration_payload(role=User.Role.ADMINISTRATOR),
    )

    assert response.status_code == 200
    assert not User.objects.filter(email="ama@example.edu").exists()
    assert "Select a valid choice" in response.content.decode()


def test_email_is_normalised_for_registration_and_sign_in(client):
    payload = registration_payload(email="Ama.Mensah@EXAMPLE.EDU")
    client.post(reverse("accounts:register"), payload)
    user = User.objects.get()
    user.approval_status = User.ApprovalStatus.ACTIVE
    user.save(update_fields=["approval_status"])

    response = client.post(
        reverse("accounts:login"),
        {"username": "ama.mensah@example.edu", "password": "SafePassword!238"},
    )

    assert user.email == "ama.mensah@example.edu"
    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")


def test_pending_user_cannot_sign_in(client):
    User.objects.create_user(
        email="pending@example.edu",
        full_name="Pending User",
        password="SafePassword!238",
        role=User.Role.LECTURER,
    )

    response = client.post(
        reverse("accounts:login"),
        {"username": "pending@example.edu", "password": "SafePassword!238"},
    )

    assert response.status_code == 200
    assert "awaiting administrator approval" in response.content.decode()
    assert "_auth_user_id" not in client.session


def test_administrator_approves_and_completes_student_setup(
    client, administrator, academic_structure
):
    student = User.objects.create_user(
        email="student@example.edu",
        full_name="Student User",
        password="SafePassword!238",
        role=User.Role.STUDENT,
    )
    client.force_login(administrator)

    approval = client.post(reverse("accounts:approve_account", args=[student.pk]))
    student.refresh_from_db()
    assert approval.status_code == 302
    assert student.approval_status == User.ApprovalStatus.ACADEMIC_SETUP

    faculty, department, programme = academic_structure
    setup = client.post(
        reverse("academics:setup", args=[student.pk]),
        {
            "faculty": faculty.pk,
            "department": department.pk,
            "programme": programme.pk,
            "student_or_staff_id": "ATU/AE/001",
        },
    )
    student.refresh_from_db()

    assert setup.status_code == 302
    assert student.approval_status == User.ApprovalStatus.ACTIVE
    assert AcademicProfile.objects.filter(user=student, programme=programme).exists()
    assert AuditEvent.objects.filter(action="ACCOUNT_APPROVED", target_id=str(student.pk)).exists()
    assert AuditEvent.objects.filter(
        action="ACADEMIC_SETUP_COMPLETED", target_id=str(student.pk)
    ).exists()


def test_student_setup_requires_programme(client, administrator, academic_structure):
    student = User.objects.create_user(
        email="student2@example.edu",
        full_name="Student Two",
        password="SafePassword!238",
        role=User.Role.STUDENT,
        approval_status=User.ApprovalStatus.ACADEMIC_SETUP,
    )
    faculty, department, _ = academic_structure
    client.force_login(administrator)

    response = client.post(
        reverse("academics:setup", args=[student.pk]),
        {
            "faculty": faculty.pk,
            "department": department.pk,
            "programme": "",
            "student_or_staff_id": "ATU/AE/002",
        },
    )

    student.refresh_from_db()
    assert response.status_code == 200
    assert "programme is required" in response.content.decode().lower()
    assert student.approval_status == User.ApprovalStatus.ACADEMIC_SETUP


@pytest.mark.parametrize(
    ("role", "expected_text"),
    [
        (User.Role.ADMINISTRATOR, "Administrator workspace"),
        (User.Role.LECTURER, "Lecturer workspace"),
        (User.Role.STUDENT, "Student workspace"),
    ],
)
def test_active_users_receive_role_dashboard(client, role, expected_text):
    user = User.objects.create_user(
        email=f"{role.lower()}@example.edu",
        full_name=f"{role.title()} User",
        password="SafePassword!238",
        role=role,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    client.force_login(user)

    response = client.get(reverse("core:dashboard"))

    assert response.status_code == 200
    assert expected_text in response.content.decode()


def test_non_administrator_cannot_open_approval_queue(client):
    lecturer = User.objects.create_user(
        email="lecturer@example.edu",
        full_name="Lecturer User",
        password="SafePassword!238",
        role=User.Role.LECTURER,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    client.force_login(lecturer)

    assert client.get(reverse("accounts:pending_approvals")).status_code == 403


def test_idle_session_is_ended_and_audited(client, administrator):
    client.force_login(administrator)
    session = client.session
    session["platform_last_activity"] = int(time.time()) - 301
    session.save()

    response = client.get(reverse("core:dashboard"))

    assert response.status_code == 302
    assert response.url == reverse("accounts:login")
    assert "_auth_user_id" not in client.session
    assert AuditEvent.objects.filter(action="SESSION_TIMEOUT", actor=administrator).exists()


def test_logout_requires_post(client, administrator):
    client.force_login(administrator)
    assert client.get(reverse("accounts:logout")).status_code == 405


def test_bootstrap_password_change_is_enforced_and_audited(client):
    administrator = User.objects.create_superuser(
        email="bootstrap@example.edu",
        full_name="Bootstrap Administrator",
        password="TemporaryPass!238",
        must_change_password=True,
    )
    client.force_login(administrator)

    dashboard = client.get(reverse("core:dashboard"))
    assert dashboard.status_code == 302
    assert dashboard.url == reverse("accounts:password_change")

    changed = client.post(
        reverse("accounts:password_change"),
        {
            "old_password": "TemporaryPass!238",
            "new_password1": "ReplacementPass!935",
            "new_password2": "ReplacementPass!935",
        },
    )
    administrator.refresh_from_db()

    assert changed.status_code == 302
    assert changed.url == reverse("core:dashboard")
    assert not administrator.must_change_password
    assert administrator.check_password("ReplacementPass!935")
    assert AuditEvent.objects.filter(action="PASSWORD_CHANGED", actor=administrator).exists()


def test_administrator_can_issue_one_time_temporary_password(client, administrator):
    lecturer = User.objects.create_user(
        email="reset@example.edu",
        full_name="Reset Lecturer",
        password="OriginalPass!238",
        role=User.Role.LECTURER,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    client.force_login(administrator)

    response = client.post(reverse("accounts:admin_password_reset", args=[lecturer.pk]))
    lecturer.refresh_from_db()
    event = AuditEvent.objects.get(action="PASSWORD_RESET_BY_ADMIN", target_id=str(lecturer.pk))

    assert response.status_code == 200
    assert lecturer.must_change_password
    assert not lecturer.check_password("OriginalPass!238")
    assert event.metadata == {"role": User.Role.LECTURER}
    assert "Temporary password issued" in response.content.decode()


def test_non_administrator_cannot_reset_password(client):
    lecturer = User.objects.create_user(
        email="resetter@example.edu",
        full_name="Resetter Lecturer",
        password="OriginalPass!238",
        role=User.Role.LECTURER,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    student = User.objects.create_user(
        email="reset-target@example.edu",
        full_name="Reset Target",
        password="OriginalPass!238",
        role=User.Role.STUDENT,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    client.force_login(lecturer)

    assert client.post(reverse("accounts:admin_password_reset", args=[student.pk])).status_code == 403
    student.refresh_from_db()
    assert student.check_password("OriginalPass!238")


def test_administrator_password_cannot_be_reset_from_user_management(client, administrator):
    other_admin = User.objects.create_superuser(
        email="other-admin@example.edu",
        full_name="Other Administrator",
        password="StrongPass!742",
    )
    client.force_login(administrator)
    assert client.post(reverse("accounts:admin_password_reset", args=[other_admin.pk])).status_code == 404
