import hashlib
import hmac
import json
import re
import secrets
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.db import transaction
from django.core import signing
from django.urls import reverse
from django.utils import timezone

from apps.auditlog.services import record_event
from apps.core.models import Notification
from apps.core.services import notify
from apps.core.services import require_administrator

from .models import (
    ApprovedResource,
    Assessment,
    EvidenceFile,
    IntegrationSession,
    PracticalSubmission,
    PracticalTask,
)


class IntegrationAuthenticationError(ValueError):
    pass


class IntegrationConflictError(ValueError):
    pass


@transaction.atomic
def approve_resource(*, resource, administrator):
    require_administrator(administrator)
    resource = ApprovedResource.objects.select_for_update().get(pk=resource.pk)
    if resource.status != ApprovedResource.Status.DRAFT:
        raise ValueError("Only draft resources can be approved.")
    resource.status = ApprovedResource.Status.APPROVED
    resource.approved_by = administrator
    resource.approved_at = timezone.now()
    resource.full_clean()
    resource.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    record_event(actor=administrator, action="RESOURCE_APPROVED", target=resource)
    return resource


def resource_has_history(resource):
    return resource.practical_tasks.exists() or resource.submission_runs.exists() or resource.integration_sessions.exists()


@transaction.atomic
def update_resource(*, resource, administrator, changes):
    require_administrator(administrator)
    resource = ApprovedResource.objects.select_for_update().get(pk=resource.pk)
    if resource.status == ApprovedResource.Status.ARCHIVED:
        raise ValueError("Restore this resource to draft before editing it.")
    if resource_has_history(resource):
        raise ValueError("This resource has task or run history. Create a new revision instead of changing the recorded resource.")
    editable = {"title", "description", "url", "version_label", "integration_mode", "integration_key_id"}
    if set(changes) - editable:
        raise ValueError("Unsupported resource field.")
    for name, value in changes.items():
        setattr(resource, name, value)
    resource.status = ApprovedResource.Status.DRAFT
    resource.approved_by = None
    resource.approved_at = None
    resource.full_clean()
    resource.save()
    record_event(actor=administrator, action="RESOURCE_UPDATED", target=resource, metadata={"approval_required": True})
    return resource


@transaction.atomic
def change_resource_availability(*, resource, administrator, action, reason):
    require_administrator(administrator)
    resource = ApprovedResource.objects.select_for_update().get(pk=resource.pk)
    if not reason.strip() or len(reason) > 500:
        raise ValueError("Provide a reason of no more than 500 characters.")
    if action == "disable" and resource.status != ApprovedResource.Status.ARCHIVED:
        resource.status = ApprovedResource.Status.ARCHIVED
        event = "RESOURCE_DISABLED"
    elif action == "restore" and resource.status == ApprovedResource.Status.ARCHIVED:
        resource.status = ApprovedResource.Status.DRAFT
        resource.approved_by = None
        resource.approved_at = None
        event = "RESOURCE_RESTORED_TO_DRAFT"
    else:
        raise ValueError("The resource state has changed. Refresh before continuing.")
    # Disabling must work even if a deployment signing secret was removed.
    # Full validation happens before fresh approval or launch.
    resource.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    record_event(actor=administrator, action=event, target=resource, metadata={"reason": reason.strip()})
    return resource


@transaction.atomic
def publish_task(*, task, lecturer):
    if task.created_by_id != lecturer.pk:
        raise ValueError("Only the task author can publish this task.")
    if task.status != PracticalTask.Status.DRAFT:
        raise ValueError("Only draft tasks can be published.")
    if not task.offering.teaching_assignments.filter(lecturer=lecturer, is_active=True).exists():
        raise ValueError("You are no longer assigned to this course offering.")
    if task.due_at <= timezone.now():
        raise ValueError("Set a future deadline before publishing.")
    if task.resources.exclude(status=ApprovedResource.Status.APPROVED).exists():
        raise ValueError("Every linked demonstration resource must be approved.")
    task.status = PracticalTask.Status.PUBLISHED
    task.published_at = timezone.now()
    task.full_clean()
    task.save(update_fields=["status", "published_at", "updated_at"])
    record_event(actor=lecturer, action="PRACTICAL_TASK_PUBLISHED", target=task)
    for enrollment in task.offering.enrollments.filter(is_active=True).select_related("student"):
        notify(
            recipient=enrollment.student,
            category=Notification.Category.TASK,
            title=f"New practical task: {task.title}",
            message=f"{task.offering.course.code} has a new practical task due {task.due_at:%d %b %Y, %H:%M}.",
            link=reverse("practicals:student_task_detail", args=[task.pk]),
        )
    return task


def _validate_student_access(*, task, student):
    if not task.offering.is_active:
        raise ValueError("This course offering is no longer active.")
    if task.status != PracticalTask.Status.PUBLISHED:
        raise ValueError("This practical task is not open for submission.")
    if not task.offering.enrollments.filter(student=student, is_active=True).exists():
        raise ValueError("You are not enrolled in this course offering.")


@transaction.atomic
def start_submission(*, task, student):
    _validate_student_access(task=task, student=student)
    if timezone.now() > task.due_at:
        raise ValueError("The submission deadline has passed.")
    submissions = task.submissions.select_for_update().filter(student=student)
    existing_draft = submissions.filter(status=PracticalSubmission.Status.DRAFT).first()
    if existing_draft:
        return existing_draft
    previous = submissions.order_by("-attempt_number").first()
    if previous is None:
        attempt_number = 1
    elif previous.status == PracticalSubmission.Status.RETURNED:
        attempt_number = previous.attempt_number + 1
        if attempt_number > task.max_resubmissions + 1:
            raise ValueError("The permitted number of resubmissions has been reached.")
    else:
        raise ValueError("A submitted attempt is already awaiting or has completed assessment.")

    submission = PracticalSubmission(
        task=task,
        student=student,
        attempt_number=attempt_number,
        response_text=previous.response_text if previous else "",
        resource=previous.resource if previous else None,
        parameter_summary=previous.parameter_summary if previous else "",
        output_summary=previous.output_summary if previous else "",
    )
    submission.full_clean()
    submission.save()
    record_event(
        actor=student,
        action="SUBMISSION_DRAFT_STARTED",
        target=submission,
        metadata={"attempt_number": attempt_number},
    )
    return submission


@transaction.atomic
def add_evidence(*, submission, student, uploaded_file):
    submission = PracticalSubmission.objects.select_for_update().get(pk=submission.pk)
    if submission.student_id != student.pk or not submission.can_edit:
        raise ValueError("Evidence can only be added to your active draft.")
    current_total = sum(submission.evidence_files.values_list("size_bytes", flat=True))
    if current_total + uploaded_file.size > settings.EVIDENCE_SUBMISSION_MAX_BYTES:
        raise ValueError("The total evidence size for one submission cannot exceed 100 MB.")
    evidence = EvidenceFile(
        submission=submission,
        file=uploaded_file,
        original_name=Path(uploaded_file.name).name,
        content_type=getattr(uploaded_file, "content_type", ""),
        size_bytes=uploaded_file.size,
    )
    evidence.full_clean()
    evidence.save()
    record_event(actor=student, action="EVIDENCE_UPLOADED", target=evidence)
    return evidence


@transaction.atomic
def remove_evidence(*, evidence, student):
    evidence = EvidenceFile.objects.select_for_update().select_related("submission").get(pk=evidence.pk)
    if evidence.submission.student_id != student.pk or not evidence.submission.can_edit:
        raise ValueError("Evidence can only be removed from your active draft.")
    record_event(actor=student, action="EVIDENCE_REMOVED", target=evidence)
    evidence.file.delete(save=False)
    evidence.delete()


@transaction.atomic
def formally_submit(*, submission, student):
    submission = PracticalSubmission.objects.select_for_update().select_related(
        "task", "resource"
    ).get(pk=submission.pk)
    if submission.student_id != student.pk or not submission.can_edit:
        raise ValueError("Only your active draft can be submitted.")
    _validate_student_access(task=submission.task, student=student)
    if timezone.now() > submission.task.due_at:
        raise ValueError("The submission deadline has passed.")
    if not submission.response_text.strip():
        raise ValueError("Enter your structured response before submitting.")
    if not submission.evidence_files.exists():
        raise ValueError("Attach at least one evidence file before submitting.")
    if submission.resource_id:
        if submission.resource.status != ApprovedResource.Status.APPROVED:
            raise ValueError("The selected demonstration resource is no longer approved.")
        submission.resource_version = submission.resource.version_label
    submission.status = (
        PracticalSubmission.Status.SUBMITTED
        if submission.attempt_number == 1
        else PracticalSubmission.Status.RESUBMITTED
    )
    submission.submitted_at = timezone.now()
    submission.full_clean()
    submission.save(
        update_fields=["status", "submitted_at", "resource_version", "updated_at"]
    )
    record_event(
        actor=student,
        action="SUBMISSION_CONFIRMED",
        target=submission,
        metadata={"attempt_number": submission.attempt_number},
    )
    return submission


def _validate_lecturer_access(*, submission, lecturer):
    if submission.task.created_by_id != lecturer.pk:
        raise ValueError("Only the task lecturer can review this submission.")
    if not submission.task.offering.teaching_assignments.filter(
        lecturer=lecturer, is_active=True
    ).exists():
        raise ValueError("You are no longer assigned to this course offering.")


@transaction.atomic
def return_for_resubmission(*, submission, lecturer, feedback):
    submission = PracticalSubmission.objects.select_for_update().select_related(
        "task", "student"
    ).get(pk=submission.pk)
    _validate_lecturer_access(submission=submission, lecturer=lecturer)
    if submission.status not in {
        PracticalSubmission.Status.SUBMITTED,
        PracticalSubmission.Status.RESUBMITTED,
    }:
        raise ValueError("Only a submitted attempt can be returned.")
    if submission.attempt_number >= submission.task.max_resubmissions + 1:
        raise ValueError("No further resubmission is permitted for this task.")
    feedback = feedback.strip()
    if not feedback:
        raise ValueError("Feedback is required when requesting a resubmission.")
    Assessment.objects.update_or_create(
        submission=submission,
        defaults={
            "lecturer": lecturer,
            "score": None,
            "feedback": feedback,
            "status": Assessment.Status.DRAFT,
            "released_at": None,
        },
    )
    submission.status = PracticalSubmission.Status.RETURNED
    submission.save(update_fields=["status", "updated_at"])
    notify(
        recipient=submission.student,
        category=Notification.Category.RESUBMISSION,
        title=f"Resubmission requested: {submission.task.title}",
        message=feedback,
        link=reverse("practicals:student_task_detail", args=[submission.task_id]),
    )
    record_event(actor=lecturer, action="SUBMISSION_RETURNED", target=submission)
    return submission


@transaction.atomic
def save_assessment(*, submission, lecturer, assessment_form):
    submission = PracticalSubmission.objects.select_for_update().select_related("task").get(
        pk=submission.pk
    )
    _validate_lecturer_access(submission=submission, lecturer=lecturer)
    if submission.status not in {
        PracticalSubmission.Status.SUBMITTED,
        PracticalSubmission.Status.RESUBMITTED,
        PracticalSubmission.Status.ASSESSED,
    }:
        raise ValueError("This submission is not ready for assessment.")
    existing = getattr(submission, "assessment", None)
    if existing and existing.status == Assessment.Status.RELEASED:
        raise ValueError("A released result cannot be changed.")
    assessment = assessment_form.save(commit=False)
    assessment.submission = submission
    assessment.lecturer = lecturer
    assessment.status = Assessment.Status.DRAFT
    assessment.full_clean()
    assessment.save()
    submission.status = PracticalSubmission.Status.ASSESSED
    submission.save(update_fields=["status", "updated_at"])
    record_event(actor=lecturer, action="ASSESSMENT_SAVED", target=assessment)
    return assessment


@transaction.atomic
def release_result(*, assessment, lecturer):
    assessment = Assessment.objects.select_for_update().select_related(
        "submission__task", "submission__student"
    ).get(pk=assessment.pk)
    _validate_lecturer_access(submission=assessment.submission, lecturer=lecturer)
    if assessment.status != Assessment.Status.DRAFT:
        raise ValueError("Only a draft assessment can be released.")
    if assessment.submission.status != PracticalSubmission.Status.ASSESSED:
        raise ValueError("Complete the assessment before releasing the result.")
    if assessment.score is None:
        raise ValueError("A score is required before result release.")
    assessment.status = Assessment.Status.RELEASED
    assessment.released_at = timezone.now()
    assessment.full_clean()
    assessment.save(update_fields=["status", "released_at", "assessed_at"])
    notify(
        recipient=assessment.submission.student,
        category=Notification.Category.RESULT,
        title=f"Result released: {assessment.submission.task.title}",
        message="Your assessment feedback and result are now available.",
        link=reverse("practicals:result_detail", args=[assessment.pk]),
    )
    record_event(actor=lecturer, action="RESULT_RELEASED", target=assessment)
    return assessment


@transaction.atomic
def create_integration_launch(*, submission, student, callback_url, completion_url):
    submission = PracticalSubmission.objects.select_for_update().select_related(
        "task", "resource"
    ).get(pk=submission.pk)
    if submission.student_id != student.pk or not submission.can_edit:
        raise ValueError("Only your active draft can launch a demonstration session.")
    _validate_student_access(task=submission.task, student=student)
    if not student.is_platform_active or not submission.task.offering.is_active:
        raise ValueError("Your academic access is no longer active.")
    if timezone.now() > submission.task.due_at:
        raise ValueError("The submission deadline has passed.")
    resource = submission.resource
    if resource is None:
        raise ValueError("Select and save a demonstration resource before launching it.")
    if resource.status != ApprovedResource.Status.APPROVED:
        raise ValueError("The selected resource is not currently approved.")
    if resource.integration_mode != ApprovedResource.IntegrationMode.SIGNED_RETURN:
        raise ValueError("This resource uses controlled-link access and has no signed return endpoint.")
    if resource.integration_key_id not in settings.INTEGRATION_SHARED_SECRETS:
        raise ValueError("The integration secret is not configured for this resource.")
    if not submission.task.resources.filter(pk=resource.pk).exists():
        raise ValueError("The selected resource is not linked to this practical task.")

    integration = IntegrationSession(
        submission=submission,
        resource=resource,
        launch_token_hash="",
        request_payload={
            "task_id": submission.task_id,
            "submission_id": submission.pk,
            "session_id": submission.run_session_id,
            "parameter_summary": submission.parameter_summary,
        },
    )
    # The signed token exposes no internal Student or submission identifiers.
    # Its database hash and session foreign keys provide submission binding.
    token_value = f"{integration.public_id}:{secrets.token_urlsafe(32)}"
    token = signing.TimestampSigner(salt="atu-integration-return").sign(token_value)
    integration.launch_token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    integration.status = IntegrationSession.Status.LAUNCHED
    integration.launched_at = timezone.now()
    integration.full_clean()
    integration.save()
    completion_url = f"{completion_url.rstrip('/')}/{integration.public_id}/"

    parts = urlsplit(resource.url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(
        {
            "atu_session": str(integration.public_id),
            "atu_return_url": callback_url,
            "atu_return_token": token,
            "atu_completion_url": completion_url,
        }
    )
    launch_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    record_event(
        actor=student,
        action="INTEGRATION_SESSION_LAUNCHED",
        target=integration,
        metadata={"resource_id": resource.pk},
    )
    return integration, launch_url


@transaction.atomic
def accept_integration_return(*, raw_body, payload, signature):
    public_id = payload.get("session_id")
    token = payload.get("return_token")
    returned_status = payload.get("status")
    outputs = payload.get("outputs")
    if not all(isinstance(value, str) and value for value in (public_id, token, returned_status)) or not isinstance(outputs, (dict, list)):
        raise ValueError("The signed return payload is incomplete.")
    integration = IntegrationSession.objects.select_for_update().select_related(
        "resource", "submission__student"
    ).get(public_id=public_id)
    if integration.status in {
        IntegrationSession.Status.COMPLETED,
        IntegrationSession.Status.FAILED,
    }:
        raise IntegrationConflictError("This integration return has already been accepted.")
    secret = settings.INTEGRATION_SHARED_SECRETS.get(integration.resource.integration_key_id)
    if not secret:
        raise IntegrationAuthenticationError("Integration authentication failed.")
    supplied = signature.removeprefix("sha256=").strip().lower()
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", supplied) or not hmac.compare_digest(supplied, expected):
        raise IntegrationAuthenticationError("Integration authentication failed.")
    if hashlib.sha256(token.encode("utf-8")).hexdigest() != integration.launch_token_hash:
        raise IntegrationAuthenticationError("Integration authentication failed.")
    try:
        unsigned = signing.TimestampSigner(salt="atu-integration-return").unsign(
            token,
            max_age=settings.INTEGRATION_RETURN_TOKEN_MAX_AGE_SECONDS,
        )
    except (signing.BadSignature, signing.SignatureExpired) as exc:
        raise IntegrationAuthenticationError("Integration authentication failed.") from exc
    if not hmac.compare_digest(unsigned.split(":", 1)[0], str(integration.public_id)):
        raise IntegrationAuthenticationError("Integration authentication failed.")
    if returned_status not in {"completed", "failed"}:
        raise ValueError("Integration status must be completed or failed.")

    submission = PracticalSubmission.objects.select_for_update().select_related(
        "task__offering", "student", "resource"
    ).get(pk=integration.submission_id)
    if not submission.can_edit:
        raise IntegrationConflictError("A confirmed submission cannot be changed by a late integration return.")
    if (
        not submission.student.is_platform_active
        or not submission.task.offering.is_active
        or submission.task.status != PracticalTask.Status.PUBLISHED
        or not submission.task.offering.enrollments.filter(student=submission.student, is_active=True).exists()
        or integration.resource.status != ApprovedResource.Status.APPROVED
        or submission.resource_id != integration.resource_id
        or not submission.task.resources.filter(pk=integration.resource_id).exists()
    ):
        raise IntegrationConflictError("Academic or demonstration-resource access is no longer valid.")

    integration.status = (
        IntegrationSession.Status.COMPLETED
        if returned_status == "completed"
        else IntegrationSession.Status.FAILED
    )
    integration.result_payload = {key: value for key, value in payload.items() if key != "return_token"}
    integration.signature_verified = True
    integration.returned_at = timezone.now()
    integration.save(
        update_fields=["status", "result_payload", "signature_verified", "returned_at"]
    )

    submission.run_session_id = str(integration.public_id)
    submission.run_status = (
        PracticalSubmission.RunStatus.COMPLETED
        if returned_status == "completed"
        else PracticalSubmission.RunStatus.FAILED
    )
    submission.output_summary = json.dumps(outputs, ensure_ascii=True)[:5000]
    submission.integration_payload = outputs
    submission.run_completed_at = timezone.now()
    submission.save(
        update_fields=[
            "run_session_id",
            "run_status",
            "output_summary",
            "integration_payload",
            "run_completed_at",
            "updated_at",
        ]
    )
    record_event(
        action="INTEGRATION_RETURN_ACCEPTED",
        target=integration,
        metadata={"status": returned_status, "signature_verified": True},
    )
    return integration
