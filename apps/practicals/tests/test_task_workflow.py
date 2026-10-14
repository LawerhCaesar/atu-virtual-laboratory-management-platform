import hashlib
import hmac
import json
from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.academics.models import (
    AcademicProfile,
    AcademicYear,
    Course,
    CourseOffering,
    Department,
    Enrollment,
    Faculty,
    Programme,
    TeachingAssignment,
)
from apps.auditlog.models import AuditEvent
from apps.core.models import Notification
from apps.practicals.forms import AssessmentForm, EvidenceUploadForm, PracticalTaskForm
from apps.practicals.models import (
    ApprovedResource,
    Assessment,
    IntegrationSession,
    PracticalSubmission,
    PracticalTask,
)
from apps.practicals.services import (
    add_evidence,
    create_integration_launch,
    formally_submit,
    publish_task,
    release_result,
    return_for_resubmission,
    save_assessment,
    start_submission,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def workflow():
    administrator = User.objects.create_superuser(
        email="admin2@example.edu", full_name="Administrator", password="StrongPass!742"
    )
    lecturer = User.objects.create_user(
        email="lecturer2@example.edu",
        full_name="Assigned Lecturer",
        password="StrongPass!742",
        role=User.Role.LECTURER,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    other_lecturer = User.objects.create_user(
        email="otherlecturer@example.edu",
        full_name="Other Lecturer",
        password="StrongPass!742",
        role=User.Role.LECTURER,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    student = User.objects.create_user(
        email="student3@example.edu",
        full_name="Enrolled Student",
        password="StrongPass!742",
        role=User.Role.STUDENT,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    other_student = User.objects.create_user(
        email="otherstudent@example.edu",
        full_name="Other Student",
        password="StrongPass!742",
        role=User.Role.STUDENT,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    faculty = Faculty.objects.create(name="Engineering and Built Environment", code="EBE")
    department = Department.objects.create(faculty=faculty, name="Automotive Engineering", code="AUT")
    programme = Programme.objects.create(department=department, name="MTech Automotive", code="MTA")
    for user, identifier in [
        (lecturer, "STAFF-001"),
        (other_lecturer, "STAFF-002"),
        (student, "STU-001"),
        (other_student, "STU-002"),
    ]:
        AcademicProfile.objects.create(
            user=user,
            faculty=faculty,
            department=department,
            programme=programme if user.role == User.Role.STUDENT else None,
            student_or_staff_id=identifier,
            configured_by=administrator,
        )
    academic_year = AcademicYear.objects.create(
        name="2026/2027",
        starts_on=timezone.localdate(),
        ends_on=timezone.localdate() + timedelta(days=300),
        is_current=True,
    )
    course = Course.objects.create(
        department=department,
        code="AUTO 701",
        title="Automotive Systems Diagnostics",
    )
    offering = CourseOffering.objects.create(
        course=course,
        programme=programme,
        academic_year=academic_year,
        semester=CourseOffering.Semester.FIRST,
    )
    TeachingAssignment.objects.create(
        offering=offering, lecturer=lecturer, assigned_by=administrator
    )
    Enrollment.objects.create(offering=offering, student=student, enrolled_by=administrator)
    approved_resource = ApprovedResource.objects.create(
        title="Approved diagnostic demonstration",
        url="https://example.edu/approved-demo",
        status=ApprovedResource.Status.APPROVED,
        created_by=administrator,
        approved_by=administrator,
        approved_at=timezone.now(),
    )
    return {
        "administrator": administrator,
        "lecturer": lecturer,
        "other_lecturer": other_lecturer,
        "student": student,
        "other_student": other_student,
        "offering": offering,
        "approved_resource": approved_resource,
    }


def task_payload(workflow, **overrides):
    data = {
        "offering": workflow["offering"].pk,
        "title": "Diagnostic evidence task",
        "instructions": "Follow the approved practical procedure.",
        "question": "Interpret the recorded diagnostic parameters.",
        "evidence_requirements": "Upload the required plot and parameter summary.",
        "due_at": (timezone.localtime() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M"),
        "max_score": "100.00",
        "max_resubmissions": "1",
        "resources": [workflow["approved_resource"].pk],
    }
    data.update(overrides)
    return data


def test_administrator_can_register_and_approve_resource(client, workflow):
    client.force_login(workflow["administrator"])
    response = client.post(
        reverse("practicals:resource_create"),
        {
            "title": "Vehicle network demonstration",
            "description": "Approved teaching demonstration.",
            "url": "https://example.edu/network-demo",
            "version_label": "v1",
        },
    )
    resource = ApprovedResource.objects.get(title="Vehicle network demonstration")
    assert response.status_code == 302
    assert resource.status == ApprovedResource.Status.DRAFT

    approval = client.post(reverse("practicals:resource_approve", args=[resource.pk]))
    resource.refresh_from_db()
    assert approval.status_code == 302
    assert resource.status == ApprovedResource.Status.APPROVED
    assert resource.approved_by == workflow["administrator"]
    assert AuditEvent.objects.filter(action="RESOURCE_APPROVED", target_id=str(resource.pk)).exists()


def test_lecturer_form_exposes_only_assigned_offerings_and_approved_resources(workflow):
    unapproved = ApprovedResource.objects.create(
        title="Unapproved draft",
        url="https://example.edu/draft",
        created_by=workflow["administrator"],
    )
    form = PracticalTaskForm(lecturer=workflow["lecturer"])
    other_form = PracticalTaskForm(lecturer=workflow["other_lecturer"])

    assert list(form.fields["offering"].queryset) == [workflow["offering"]]
    assert workflow["approved_resource"] in form.fields["resources"].queryset
    assert unapproved not in form.fields["resources"].queryset
    assert not other_form.fields["offering"].queryset.exists()


def test_assigned_lecturer_can_create_and_publish_task(client, workflow):
    client.force_login(workflow["lecturer"])
    created = client.post(reverse("practicals:task_create"), task_payload(workflow))
    task = PracticalTask.objects.get(title="Diagnostic evidence task")

    assert created.status_code == 302
    assert task.status == PracticalTask.Status.DRAFT
    assert list(task.resources.all()) == [workflow["approved_resource"]]

    published = client.post(reverse("practicals:task_publish", args=[task.pk]))
    task.refresh_from_db()
    assert published.status_code == 302
    assert task.status == PracticalTask.Status.PUBLISHED
    assert task.published_at is not None
    assert AuditEvent.objects.filter(action="PRACTICAL_TASK_PUBLISHED", target_id=str(task.pk)).exists()


def test_publishing_rejects_past_deadline(workflow):
    task = PracticalTask.objects.create(
        offering=workflow["offering"],
        title="Expired draft",
        instructions="Instructions",
        question="Question",
        evidence_requirements="Evidence",
        due_at=timezone.now() - timedelta(minutes=1),
        max_score=50,
        created_by=workflow["lecturer"],
    )
    with pytest.raises(ValueError, match="future deadline"):
        publish_task(task=task, lecturer=workflow["lecturer"])


def test_only_enrolled_student_can_view_published_task(client, workflow):
    task = PracticalTask.objects.create(
        offering=workflow["offering"],
        title="Published task",
        instructions="Instructions",
        question="Question",
        evidence_requirements="Evidence",
        due_at=timezone.now() + timedelta(days=5),
        max_score=50,
        created_by=workflow["lecturer"],
        status=PracticalTask.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    client.force_login(workflow["student"])
    assert client.get(reverse("practicals:student_task_detail", args=[task.pk])).status_code == 200

    client.force_login(workflow["other_student"])
    assert client.get(reverse("practicals:student_task_detail", args=[task.pk])).status_code == 404


def test_other_lecturer_cannot_edit_task(client, workflow):
    task = PracticalTask.objects.create(
        offering=workflow["offering"],
        title="Owned draft",
        instructions="Instructions",
        question="Question",
        evidence_requirements="Evidence",
        due_at=timezone.now() + timedelta(days=5),
        max_score=50,
        created_by=workflow["lecturer"],
    )
    client.force_login(workflow["other_lecturer"])
    assert client.get(reverse("practicals:task_edit", args=[task.pk])).status_code == 404


def test_course_offering_rejects_cross_department_programme(workflow):
    other_faculty = Faculty.objects.create(name="Applied Sciences", code="AS")
    other_department = Department.objects.create(
        faculty=other_faculty, name="Computer Science", code="CS"
    )
    other_programme = Programme.objects.create(
        department=other_department, name="MTech Computing", code="MTC"
    )
    offering = CourseOffering(
        course=workflow["offering"].course,
        programme=other_programme,
        academic_year=workflow["offering"].academic_year,
        semester=CourseOffering.Semester.SECOND,
    )
    with pytest.raises(ValidationError):
        offering.full_clean()


def make_submitted_attempt(workflow, tmp_path, *, title="Submission task"):
    task = PracticalTask.objects.create(
        offering=workflow["offering"],
        title=title,
        instructions="Instructions",
        question="Question",
        evidence_requirements="Evidence",
        due_at=timezone.now() + timedelta(days=5),
        max_score=100,
        max_resubmissions=1,
        created_by=workflow["lecturer"],
        status=PracticalTask.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    task.resources.add(workflow["approved_resource"])
    submission = start_submission(task=task, student=workflow["student"])
    submission.response_text = "A structured interpretation of the diagnostic evidence."
    submission.resource = workflow["approved_resource"]
    submission.parameter_summary = "engine_speed=1500 rpm"
    submission.run_session_id = "RUN-001"
    submission.run_status = PracticalSubmission.RunStatus.COMPLETED
    submission.output_summary = "The requested output was generated."
    submission.save()
    with override_settings(MEDIA_ROOT=tmp_path):
        add_evidence(
            submission=submission,
            student=workflow["student"],
            uploaded_file=SimpleUploadedFile(
                "parameter-summary.txt", b"engine_speed=1500", content_type="text/plain"
            ),
        )
        formally_submit(submission=submission, student=workflow["student"])
    submission.refresh_from_db()
    return task, submission


def test_student_can_upload_evidence_and_formally_submit(workflow, tmp_path):
    task, submission = make_submitted_attempt(workflow, tmp_path)

    assert submission.status == PracticalSubmission.Status.SUBMITTED
    assert submission.submitted_at is not None
    assert submission.resource_version == workflow["approved_resource"].version_label
    assert submission.evidence_files.get().original_name == "parameter-summary.txt"
    assert AuditEvent.objects.filter(
        action="SUBMISSION_CONFIRMED", target_id=str(submission.pk)
    ).exists()
    assert task.submissions.count() == 1


def test_formal_submission_requires_response_and_evidence(workflow):
    task = PracticalTask.objects.create(
        offering=workflow["offering"],
        title="Incomplete task",
        instructions="Instructions",
        question="Question",
        evidence_requirements="Evidence",
        due_at=timezone.now() + timedelta(days=2),
        max_score=20,
        created_by=workflow["lecturer"],
        status=PracticalTask.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    submission = start_submission(task=task, student=workflow["student"])
    with pytest.raises(ValueError, match="structured response"):
        formally_submit(submission=submission, student=workflow["student"])
    submission.response_text = "Response"
    submission.save()
    with pytest.raises(ValueError, match="evidence file"):
        formally_submit(submission=submission, student=workflow["student"])


def test_evidence_form_rejects_unsupported_type_and_oversized_file():
    unsupported = EvidenceUploadForm(
        files={"file": SimpleUploadedFile("archive.exe", b"content", content_type="application/octet-stream")}
    )
    assert not unsupported.is_valid()

    with override_settings(EVIDENCE_FILE_MAX_BYTES=3):
        oversized = EvidenceUploadForm(
            files={"file": SimpleUploadedFile("large.txt", b"four", content_type="text/plain")}
        )
        assert not oversized.is_valid()
        assert "20 MB" in oversized.errors["file"][0]

    disguised_pdf = EvidenceUploadForm(
        files={"file": SimpleUploadedFile("evidence.pdf", b"not a pdf", content_type="application/pdf")}
    )
    assert not disguised_pdf.is_valid()
    assert "does not match" in disguised_pdf.errors["file"][0]


def test_submission_total_evidence_limit_is_enforced(workflow, tmp_path):
    task = PracticalTask.objects.create(
        offering=workflow["offering"],
        title="Evidence limit task",
        instructions="Instructions",
        question="Question",
        evidence_requirements="Evidence",
        due_at=timezone.now() + timedelta(days=2),
        max_score=20,
        created_by=workflow["lecturer"],
        status=PracticalTask.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    submission = start_submission(task=task, student=workflow["student"])
    with override_settings(MEDIA_ROOT=tmp_path, EVIDENCE_SUBMISSION_MAX_BYTES=5):
        add_evidence(
            submission=submission,
            student=workflow["student"],
            uploaded_file=SimpleUploadedFile("first.txt", b"1234", content_type="text/plain"),
        )
        with pytest.raises(ValueError, match="100 MB"):
            add_evidence(
                submission=submission,
                student=workflow["student"],
                uploaded_file=SimpleUploadedFile("second.txt", b"12", content_type="text/plain"),
            )


def test_lecturer_can_return_and_student_can_start_one_resubmission(workflow, tmp_path):
    task, first = make_submitted_attempt(workflow, tmp_path, title="Resubmission task")
    returned = return_for_resubmission(
        submission=first,
        lecturer=workflow["lecturer"],
        feedback="Clarify the parameter interpretation.",
    )
    second = start_submission(task=task, student=workflow["student"])

    assert returned.status == PracticalSubmission.Status.RETURNED
    assert returned.assessment.feedback == "Clarify the parameter interpretation."
    assert second.attempt_number == 2
    assert second.response_text == first.response_text
    assert Notification.objects.filter(
        recipient=workflow["student"], category=Notification.Category.RESUBMISSION
    ).exists()

    second.status = PracticalSubmission.Status.RETURNED
    second.save(update_fields=["status"])
    with pytest.raises(ValueError, match="permitted number"):
        start_submission(task=task, student=workflow["student"])


def test_assessment_is_private_until_lecturer_releases_it(client, workflow, tmp_path):
    _, submission = make_submitted_attempt(workflow, tmp_path, title="Assessment task")
    form = AssessmentForm(
        {"score": "78.50", "feedback": "Clear evidence and a defensible interpretation."},
        submission=submission,
    )
    assert form.is_valid(), form.errors
    assessment = save_assessment(
        submission=submission,
        lecturer=workflow["lecturer"],
        assessment_form=form,
    )

    client.force_login(workflow["student"])
    hidden = client.get(reverse("practicals:result_detail", args=[assessment.pk]))
    assert hidden.status_code == 404

    release_result(assessment=assessment, lecturer=workflow["lecturer"])
    assessment.refresh_from_db()
    visible = client.get(reverse("practicals:result_detail", args=[assessment.pk]))

    assert assessment.status == Assessment.Status.RELEASED
    assert visible.status_code == 200
    assert "78.50" in visible.content.decode()
    assert Notification.objects.filter(
        recipient=workflow["student"], category=Notification.Category.RESULT
    ).exists()
    assert AuditEvent.objects.filter(action="RESULT_RELEASED", target_id=str(assessment.pk)).exists()


def test_assessment_score_cannot_exceed_task_maximum(workflow, tmp_path):
    _, submission = make_submitted_attempt(workflow, tmp_path, title="Maximum score task")
    form = AssessmentForm(
        {"score": "100.01", "feedback": "Invalid score"}, submission=submission
    )
    assert not form.is_valid()
    assert "cannot exceed" in form.errors["score"][0]


def test_other_lecturer_cannot_assess_submission(workflow, tmp_path):
    _, submission = make_submitted_attempt(workflow, tmp_path, title="Protected assessment task")
    form = AssessmentForm(
        {"score": "50", "feedback": "Feedback"}, submission=submission
    )
    assert form.is_valid()
    with pytest.raises(ValueError, match="task lecturer"):
        save_assessment(
            submission=submission,
            lecturer=workflow["other_lecturer"],
            assessment_form=form,
        )


def test_protected_evidence_download_enforces_ownership(client, workflow, tmp_path):
    _, submission = make_submitted_attempt(workflow, tmp_path, title="Download task")
    evidence = submission.evidence_files.get()

    with override_settings(MEDIA_ROOT=tmp_path):
        client.force_login(workflow["student"])
        own_response = client.get(reverse("practicals:evidence_download", args=[evidence.pk]))
        assert own_response.status_code == 200
        own_response.close()

        client.force_login(workflow["other_student"])
        assert client.get(reverse("practicals:evidence_download", args=[evidence.pk])).status_code == 403

        client.force_login(workflow["lecturer"])
        lecturer_response = client.get(reverse("practicals:evidence_download", args=[evidence.pk]))
        assert lecturer_response.status_code == 200
        lecturer_response.close()


def test_notification_cannot_be_opened_by_another_user(client, workflow):
    notification = Notification.objects.create(
        recipient=workflow["student"],
        category=Notification.Category.SYSTEM,
        title="Private notification",
        message="Private",
        link="/dashboard/",
    )
    client.force_login(workflow["other_student"])
    assert client.get(reverse("core:notification_open", args=[notification.pk])).status_code == 404


def make_integration_draft(workflow):
    resource = ApprovedResource.objects.create(
        title="Signed demonstration",
        url="https://demo.example.edu/launch?mode=teaching",
        version_label="2.0",
        status=ApprovedResource.Status.APPROVED,
        integration_mode=ApprovedResource.IntegrationMode.SIGNED_RETURN,
        integration_key_id="demo-key",
        created_by=workflow["administrator"],
        approved_by=workflow["administrator"],
        approved_at=timezone.now(),
    )
    task = PracticalTask.objects.create(
        offering=workflow["offering"],
        title="Signed return task",
        instructions="Instructions",
        question="Question",
        evidence_requirements="Evidence",
        due_at=timezone.now() + timedelta(days=2),
        max_score=100,
        created_by=workflow["lecturer"],
        status=PracticalTask.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    task.resources.add(resource)
    submission = start_submission(task=task, student=workflow["student"])
    submission.resource = resource
    submission.parameter_summary = "mass=1200 kg; speed=20 m/s"
    submission.save()
    return resource, submission


def test_signed_resource_requires_configured_external_secret(workflow):
    resource = ApprovedResource(
        title="Unconfigured signed resource",
        url="https://demo.example.edu/",
        integration_mode=ApprovedResource.IntegrationMode.SIGNED_RETURN,
        integration_key_id="missing-key",
        created_by=workflow["administrator"],
    )
    with override_settings(INTEGRATION_SHARED_SECRETS={}):
        with pytest.raises(ValidationError, match="No shared secret"):
            resource.full_clean()


@pytest.mark.parametrize("field,bad_value", [("session_id", []), ("return_token", 123), ("status", ["completed"]), ("outputs", "invalid")])
def test_callback_rejects_malformed_field_types(client, field, bad_value):
    payload = {"session_id": "invalid", "return_token": "token", "status": "completed", "outputs": {}}
    payload[field] = bad_value
    response = client.post(reverse("practicals:integration_return"), data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 400


@pytest.mark.parametrize("invalid_state", ["confirmed", "unenrolled", "archived_resource", "changed_resource"])
def test_late_or_revoked_signed_return_cannot_change_draft(client, workflow, invalid_state):
    secret = "test-only-shared-secret-for-immutable-submissions"
    with override_settings(INTEGRATION_SHARED_SECRETS={"demo-key": secret}):
        resource, submission = make_integration_draft(workflow)
        integration, launch_url = create_integration_launch(
            submission=submission, student=workflow["student"],
            callback_url="http://testserver/practicals/integrations/return/",
            completion_url="http://testserver/practicals/integrations/sessions/",
        )
        payload = {"session_id": str(integration.public_id), "return_token": parse_qs(urlsplit(launch_url).query)["atu_return_token"][0], "status": "completed", "outputs": {"new_value": 42}}
        raw = json.dumps(payload).encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
        if invalid_state == "confirmed":
            submission.status = PracticalSubmission.Status.SUBMITTED
            submission.save(update_fields=["status"])
        elif invalid_state == "unenrolled":
            submission.task.offering.enrollments.filter(student=workflow["student"]).update(is_active=False)
        elif invalid_state == "archived_resource":
            resource.status = ApprovedResource.Status.ARCHIVED
            resource.save(update_fields=["status"])
        else:
            submission.resource = None
            submission.save(update_fields=["resource"])
        response = client.post(reverse("practicals:integration_return"), data=raw, content_type="application/json", HTTP_X_ATU_SIGNATURE=f"sha256={digest}")
        assert response.status_code == 409
        submission.refresh_from_db()
        integration.refresh_from_db()
        assert submission.integration_payload == {}
        assert not integration.signature_verified


def test_expired_signed_token_is_rejected(client, workflow):
    secret = "test-only-shared-secret-for-expiration"
    with override_settings(INTEGRATION_SHARED_SECRETS={"demo-key": secret}):
        _, submission = make_integration_draft(workflow)
        integration, launch_url = create_integration_launch(submission=submission, student=workflow["student"], callback_url="http://testserver/callback/", completion_url="http://testserver/status/")
        payload = {"session_id": str(integration.public_id), "return_token": parse_qs(urlsplit(launch_url).query)["atu_return_token"][0], "status": "completed", "outputs": {}}
        raw = json.dumps(payload).encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
        with override_settings(INTEGRATION_RETURN_TOKEN_MAX_AGE_SECONDS=-1):
            response = client.post(reverse("practicals:integration_return"), data=raw, content_type="application/json", HTTP_X_ATU_SIGNATURE=digest)
        assert response.status_code == 403


def test_signed_integration_return_updates_only_bound_draft(client, workflow):
    secret = "local-test-shared-secret-that-is-not-stored-in-the-database"
    with override_settings(INTEGRATION_SHARED_SECRETS={"demo-key": secret}):
        resource, submission = make_integration_draft(workflow)
        integration, launch_url = create_integration_launch(
            submission=submission,
            student=workflow["student"],
            callback_url="http://testserver/practicals/integrations/return/",
            completion_url="http://testserver/practicals/integrations/sessions/",
        )
        query = parse_qs(urlsplit(launch_url).query)
        token = query["atu_return_token"][0]

        assert query["mode"] == ["teaching"]
        assert query["atu_session"] == [str(integration.public_id)]
        assert str(integration.public_id) in query["atu_completion_url"][0]
        assert workflow["student"].email not in launch_url
        assert resource.integration_key_id not in launch_url

        payload = {
            "session_id": str(integration.public_id),
            "return_token": token,
            "status": "completed",
            "outputs": {"peak_speed": 31.4, "plot_reference": "plot-001"},
        }
        raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        response = client.post(
            reverse("practicals:integration_return"),
            data=raw_body,
            content_type="application/json",
            HTTP_X_ATU_SIGNATURE=f"sha256={signature}",
        )

        integration.refresh_from_db()
        submission.refresh_from_db()
        assert response.status_code == 200
        assert response.json()["accepted"] is True
        assert integration.status == IntegrationSession.Status.COMPLETED
        assert integration.signature_verified
        assert "return_token" not in integration.result_payload
        assert submission.run_status == PracticalSubmission.RunStatus.COMPLETED
        assert submission.integration_payload == payload["outputs"]
        assert AuditEvent.objects.filter(
            action="INTEGRATION_RETURN_ACCEPTED", target_id=str(integration.pk)
        ).exists()


def test_integration_return_rejects_bad_signature_and_replay(client, workflow):
    secret = "another-local-test-secret"
    with override_settings(INTEGRATION_SHARED_SECRETS={"demo-key": secret}):
        _, submission = make_integration_draft(workflow)
        integration, launch_url = create_integration_launch(
            submission=submission,
            student=workflow["student"],
            callback_url="http://testserver/practicals/integrations/return/",
            completion_url="http://testserver/practicals/integrations/sessions/",
        )
        token = parse_qs(urlsplit(launch_url).query)["atu_return_token"][0]
        payload = {
            "session_id": str(integration.public_id),
            "return_token": token,
            "status": "failed",
            "outputs": {"error_code": "DEMO_FAILURE"},
        }
        raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        bad = client.post(
            reverse("practicals:integration_return"),
            data=raw_body,
            content_type="application/json",
            HTTP_X_ATU_SIGNATURE="sha256=00",
        )
        assert bad.status_code == 403
        integration.refresh_from_db()
        assert integration.status == IntegrationSession.Status.LAUNCHED

        signature = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        accepted = client.post(
            reverse("practicals:integration_return"),
            data=raw_body,
            content_type="application/json",
            HTTP_X_ATU_SIGNATURE=signature,
        )
        replay = client.post(
            reverse("practicals:integration_return"),
            data=raw_body,
            content_type="application/json",
            HTTP_X_ATU_SIGNATURE=signature,
        )
        assert accepted.status_code == 200
        assert replay.status_code == 409


def test_integration_callback_enforces_payload_limit(client):
    with override_settings(INTEGRATION_CALLBACK_MAX_BYTES=10):
        response = client.post(
            reverse("practicals:integration_return"),
            data=b'{"payload":"larger than ten bytes"}',
            content_type="application/json",
        )
    assert response.status_code == 413
