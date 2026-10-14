from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.academics.models import AcademicYear, Course, CourseOffering, Department, Faculty, Programme
from apps.auditlog.models import AuditEvent
from apps.practicals.models import Assessment, PracticalSubmission, PracticalTask


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("value", ["=1+1", "+SUM(A1)", "-1", "@formula", "\t=1+1", "  =1+1", "\nvalue"])
def test_csv_formula_guard_handles_whitespace_and_controls(value):
    from apps.reporting.services import _safe_csv
    assert _safe_csv(value).startswith("'")


@pytest.fixture
def report_records():
    administrator = User.objects.create_superuser(
        email="report-admin@example.edu",
        full_name="Report Administrator",
        password="StrongPass!742",
    )
    lecturer = User.objects.create_user(
        email="report-lecturer@example.edu",
        full_name="Report Lecturer",
        password="StrongPass!742",
        role=User.Role.LECTURER,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    student = User.objects.create_user(
        email="report-student@example.edu",
        full_name="=FORMULA Student",
        password="StrongPass!742",
        role=User.Role.STUDENT,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    faculty = Faculty.objects.create(name="Reporting Faculty", code="RF")
    department = Department.objects.create(faculty=faculty, name="Reporting Department", code="RD")
    programme = Programme.objects.create(department=department, name="Reporting Programme", code="RP")
    year = AcademicYear.objects.create(
        name="2030/2031",
        starts_on=timezone.localdate(),
        ends_on=timezone.localdate() + timedelta(days=300),
    )
    course = Course.objects.create(department=department, code="AUTO-R1", title="Report Course")
    offering = CourseOffering.objects.create(
        course=course,
        programme=programme,
        academic_year=year,
        semester=CourseOffering.Semester.FIRST,
    )
    task = PracticalTask.objects.create(
        offering=offering,
        title="Report Task",
        instructions="Instructions",
        question="Question",
        evidence_requirements="Evidence",
        due_at=timezone.now() + timedelta(days=2),
        max_score=100,
        created_by=lecturer,
        status=PracticalTask.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    submission = PracticalSubmission.objects.create(
        task=task,
        student=student,
        attempt_number=1,
        status=PracticalSubmission.Status.ASSESSED,
        response_text="Response",
        submitted_at=timezone.now(),
    )
    assessment = Assessment.objects.create(
        submission=submission,
        lecturer=lecturer,
        score=81,
        feedback="Released feedback",
        status=Assessment.Status.RELEASED,
        released_at=timezone.now(),
    )
    AuditEvent.objects.create(
        actor=administrator,
        action="REPORT_TEST_EVENT",
        target_type="practicals.PracticalSubmission",
        target_id=str(submission.pk),
    )
    return {
        "administrator": administrator,
        "lecturer": lecturer,
        "student": student,
        "offering": offering,
        "submission": submission,
        "assessment": assessment,
    }


def test_report_dashboard_is_administrator_only(client, report_records):
    client.force_login(report_records["administrator"])
    response = client.get(reverse("reporting:dashboard"))
    assert response.status_code == 200
    assert "Reports and exports" in response.content.decode()
    assert "Report Task" in response.content.decode()

    client.force_login(report_records["lecturer"])
    assert client.get(reverse("reporting:dashboard")).status_code == 403


def test_users_csv_neutralises_spreadsheet_formula_cells(client, report_records):
    client.force_login(report_records["administrator"])
    response = client.get(reverse("reporting:users_csv"))
    text = response.content.decode("utf-8-sig")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "attachment" in response["Content-Disposition"]
    assert "'=FORMULA Student" in text


def test_submission_csv_contains_only_released_score(client, report_records):
    client.force_login(report_records["administrator"])
    response = client.get(
        reverse("reporting:submissions_csv"), {"offering": report_records["offering"].pk}
    )
    text = response.content.decode("utf-8-sig")

    assert response.status_code == 200
    assert "Report Task" in text
    assert "81.00" in text


def test_audit_report_filters_and_exports(client, report_records):
    client.force_login(report_records["administrator"])
    page = client.get(reverse("reporting:audit"), {"action": "REPORT_TEST_EVENT"})
    export = client.get(reverse("reporting:audit_csv"), {"action": "REPORT_TEST_EVENT"})

    assert page.status_code == 200
    assert "REPORT_TEST_EVENT" in page.content.decode()
    assert export.status_code == 200
    assert "REPORT_TEST_EVENT" in export.content.decode("utf-8-sig")


def test_summary_pdf_has_valid_response_and_development_label(client, report_records):
    client.force_login(report_records["administrator"])
    response = client.get(reverse("reporting:summary_pdf"))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 2000
    assert "attachment" in response["Content-Disposition"]
