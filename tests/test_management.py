import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import change_account_availability
from apps.auditlog.models import AuditEvent
from apps.core.forms import AdministratorNoticeForm
from apps.core.models import AdministratorNotice, Notification, PlatformSettings, SupportRequest
from apps.core.services import cancel_notice, send_notice
from apps.practicals.models import ApprovedResource, PracticalTask
from apps.practicals.services import add_evidence, approve_resource, change_resource_availability, create_integration_launch, formally_submit, start_submission, update_resource
from apps.practicals.tests.test_task_workflow import workflow, task_payload


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def fast_passwords(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def resource_payload(resource, **changes):
    payload = {field: getattr(resource, field) for field in ["title", "description", "url", "version_label", "integration_mode", "integration_key_id"]}
    payload.update(changes)
    return payload


def draft_notice(workflow, **changes):
    values = {"title": "Synthetic maintenance notice", "message": "Non-research operational example.", "audience": AdministratorNotice.Audience.STUDENT, "created_by": workflow["administrator"], "link": "/help/"}
    values.update(changes)
    return AdministratorNotice.objects.create(**values)


@pytest.mark.parametrize("role", ["student", "lecturer"])
@pytest.mark.parametrize("route", ["core:platform_settings", "core:notice_management", "core:notice_create", "core:support_management", "practicals:resource_list", "accounts:user_management"])
def test_management_is_administrator_only(client, workflow, role, route):
    client.force_login(workflow[role])
    assert client.get(reverse(route)).status_code == 403
    assert client.post(reverse(route), {"title": "Unauthorised"}).status_code == 403
    assert not AdministratorNotice.objects.exists()
    assert not PlatformSettings.objects.exists()


def test_settings_get_is_read_only_and_post_is_audited_and_escaped(client, workflow):
    client.force_login(workflow["administrator"])
    assert client.get(reverse("core:platform_settings")).status_code == 200
    assert not PlatformSettings.objects.exists()
    response = client.post(reverse("core:platform_settings"), {"support_email": "support@example.edu", "support_hours": "Weekdays", "help_message": "<script>unsafe()</script>"})
    assert response.status_code == 302
    record = PlatformSettings.objects.get(pk=1)
    assert record.updated_by == workflow["administrator"]
    assert AuditEvent.objects.filter(action="PLATFORM_SETTINGS_UPDATED").exists()
    client.logout()
    html = client.get(reverse("core:help")).content.decode()
    assert "support@example.edu" in html
    assert "&lt;script&gt;unsafe()&lt;/script&gt;" in html
    assert "<script>unsafe()" not in html
    assert PlatformSettings.objects.count() == 1


def test_resource_edit_requires_fresh_approval(client, workflow):
    client.force_login(workflow["administrator"])
    resource = workflow["approved_resource"]
    assert client.post(reverse("practicals:resource_edit", args=[resource.pk]), resource_payload(resource, title="Updated controlled resource")).status_code == 302
    resource.refresh_from_db()
    assert resource.status == resource.Status.DRAFT
    assert resource.approved_by is None and resource.approved_at is None
    assert AuditEvent.objects.filter(action="RESOURCE_UPDATED").exists()
    approve_resource(resource=resource, administrator=workflow["administrator"])
    resource.refresh_from_db()
    assert resource.status == resource.Status.APPROVED


def test_resource_with_task_history_cannot_be_edited_but_can_be_revised(client, workflow):
    resource = workflow["approved_resource"]
    payload = task_payload(workflow)
    task = PracticalTask.objects.create(offering=workflow["offering"], created_by=workflow["lecturer"], title=payload["title"], instructions=payload["instructions"], question=payload["question"], evidence_requirements=payload["evidence_requirements"], due_at=timezone.now() + timedelta(days=7), max_score=100)
    task.resources.add(resource)
    client.force_login(workflow["administrator"])
    original_url = resource.url
    with pytest.raises(ValueError, match="history"):
        update_resource(resource=resource, administrator=workflow["administrator"], changes={"url": "https://example.edu/changed"})
    response = client.post(reverse("practicals:resource_edit", args=[resource.pk]), resource_payload(resource, url="https://example.edu/changed"))
    assert response.status_code == 302
    resource.refresh_from_db()
    assert resource.url == original_url
    response = client.post(reverse("practicals:resource_revision", args=[resource.pk]), resource_payload(resource, version_label="v2", url="https://example.edu/new-revision"))
    assert response.status_code == 302
    revision = resource.revisions.get()
    assert revision.status == ApprovedResource.Status.DRAFT
    assert task.resources.get() == resource
    assert AuditEvent.objects.filter(action="RESOURCE_REVISION_CREATED", target_id=str(revision.pk)).exists()


def test_revision_requires_distinct_version(client, workflow):
    client.force_login(workflow["administrator"])
    resource = workflow["approved_resource"]
    response = client.post(reverse("practicals:resource_revision", args=[resource.pk]), resource_payload(resource))
    assert response.status_code == 200
    assert "version_label" in response.context["form"].errors
    assert not resource.revisions.exists()


def test_resource_disable_confirmation_restore_and_no_get_mutation(client, workflow):
    client.force_login(workflow["administrator"])
    resource = workflow["approved_resource"]
    url = reverse("practicals:resource_availability", args=[resource.pk, "disable"])
    assert client.get(url).status_code == 200
    assert client.post(url, {"reason": "Needs maintenance"}).status_code == 200
    resource.refresh_from_db()
    assert resource.status == resource.Status.APPROVED
    assert client.post(url, {"reason": "Needs maintenance", "confirm": "on"}).status_code == 302
    resource.refresh_from_db()
    assert resource.status == resource.Status.ARCHIVED
    with pytest.raises(ValueError, match="draft"):
        approve_resource(resource=resource, administrator=workflow["administrator"])
    assert client.post(reverse("practicals:resource_availability", args=[resource.pk, "restore"]), {"reason": "Maintenance completed", "confirm": "on"}).status_code == 302
    resource.refresh_from_db()
    assert resource.status == resource.Status.DRAFT
    assert resource.approved_by is None
    assert AuditEvent.objects.filter(action="RESOURCE_DISABLED").get().metadata["reason"] == "Needs maintenance"


@pytest.mark.parametrize("role", ["student", "lecturer"])
def test_resource_service_requires_active_administrator(workflow, role):
    with pytest.raises(ValueError, match="Administrator"):
        change_resource_availability(resource=workflow["approved_resource"], administrator=workflow[role], action="disable", reason="Unauthorised")


def test_notice_draft_preview_send_and_replay(client, workflow):
    client.force_login(workflow["administrator"])
    response = client.post(reverse("core:notice_create"), {"title": "Example notice", "message": "Example", "audience": "STUDENT", "link": "/help/"})
    assert response.status_code == 302
    notice = AdministratorNotice.objects.get()
    assert notice.sent_at is None and notice.deliveries.count() == 0
    send_url = reverse("core:notice_send", args=[notice.pk])
    assert client.get(send_url).status_code == 405
    assert client.get(reverse("core:notice_detail", args=[notice.pk])).context["recipient_count"] == 2
    assert client.post(send_url).status_code == 302
    assert set(notice.deliveries.values_list("recipient_id", flat=True)) == {workflow["student"].pk, workflow["other_student"].pk}
    assert client.post(send_url).status_code == 302
    assert notice.deliveries.count() == 2
    assert AuditEvent.objects.filter(action="ADMIN_NOTICE_SENT").count() == 1
    assert client.get(reverse("core:notice_management")).status_code == 200


def test_notice_checks_current_recipient_eligibility_and_no_empty_send(workflow):
    notice = draft_notice(workflow, audience="INDIVIDUAL", recipient=workflow["student"])
    workflow["student"].approval_status = User.ApprovalStatus.SUSPENDED
    workflow["student"].save(update_fields=["approval_status"])
    with pytest.raises(ValueError, match="No active recipients"):
        send_notice(notice=notice, administrator=workflow["administrator"])
    notice.refresh_from_db()
    assert notice.sent_at is None and notice.deliveries.count() == 0


def test_notice_cancellation_is_retained_and_blocks_delivery(workflow):
    notice = draft_notice(workflow)
    cancel_notice(notice=notice, administrator=workflow["administrator"])
    with pytest.raises(ValueError, match="draft"):
        send_notice(notice=notice, administrator=workflow["administrator"])
    assert AdministratorNotice.objects.filter(pk=notice.pk, cancelled_at__isnull=False).exists()
    assert not notice.deliveries.exists()


@pytest.mark.parametrize("link", ["//evil.example/", "/\\evil.example/", "/%2fevil.example/", "https://evil.example/", "/%0aevil", "/missing-route/"])
def test_notice_rejects_unsafe_or_missing_link(workflow, link):
    form = AdministratorNoticeForm({"title": "Example", "message": "Example", "audience": "STUDENT", "link": link})
    assert not form.is_valid() and "link" in form.errors


def test_notification_redirect_guards_legacy_unsafe_records(client, workflow):
    notification = Notification.objects.create(recipient=workflow["student"], category="SYSTEM", title="Legacy", message="Example", link="//evil.example/")
    with pytest.raises(ValidationError):
        notification.full_clean()
    client.force_login(workflow["student"])
    assert client.get(reverse("core:notification_open", args=[notification.pk])).url == reverse("core:dashboard")


def test_support_request_privacy_response_and_notification(client, workflow):
    client.force_login(workflow["student"])
    assert client.post(reverse("core:help"), {"subject": "Example access question", "message": "How do I use the resource?"}).status_code == 302
    ticket = SupportRequest.objects.get()
    client.force_login(workflow["other_student"])
    assert "Example access question" not in client.get(reverse("core:help")).content.decode()
    assert client.get(reverse("core:support_review", args=[ticket.pk])).status_code == 403
    client.force_login(workflow["administrator"])
    assert client.get(reverse("core:support_management")).status_code == 200
    assert client.post(reverse("core:support_review", args=[ticket.pk]), {"status": "RESOLVED", "response": "Open the assigned task and select its approved resource."}).status_code == 302
    ticket.refresh_from_db()
    assert ticket.status == "RESOLVED" and ticket.reviewed_by == workflow["administrator"]
    assert Notification.objects.filter(recipient=workflow["student"], link="/help/").exists()
    client.force_login(workflow["student"])
    assert "Open the assigned task" in client.get(reverse("core:help")).content.decode()


def test_anonymous_support_post_is_denied(client):
    assert client.get(reverse("core:help")).status_code == 200
    assert client.post(reverse("core:help"), {"subject": "Spam", "message": "Example"}).status_code == 403
    assert not SupportRequest.objects.exists()


def test_suspension_and_reactivation_revoke_even_unvisited_old_sessions(client, workflow):
    student = workflow["student"]
    first = Client()
    second = Client()
    first.force_login(student)
    second.force_login(student)
    original_hash = student.get_session_auth_hash()
    client.force_login(workflow["administrator"])
    url = reverse("accounts:account_availability", args=[student.pk, "suspend"])
    assert client.get(url).status_code == 200
    student.refresh_from_db()
    assert student.is_platform_active
    assert client.post(url, {"reason": "Example review", "confirm": "on"}).status_code == 302
    student.refresh_from_db()
    assert not student.is_active and student.approval_status == "SUSPENDED"
    assert student.get_session_auth_hash() != original_hash
    assert first.get(reverse("core:dashboard")).status_code == 302
    assert client.post(reverse("accounts:account_availability", args=[student.pk, "reactivate"]), {"reason": "Review completed", "confirm": "on"}).status_code == 302
    student.refresh_from_db()
    assert student.is_platform_active
    # Second session did not make any request during suspension; it is still invalid.
    assert second.get(reverse("core:dashboard")).status_code == 302
    assert second.login(email=student.email, password="StrongPass!742")
    assert second.get(reverse("core:dashboard")).status_code == 200
    assert student.academic_profile is not None
    assert AuditEvent.objects.filter(action__in=["ACCOUNT_SUSPENDED", "ACCOUNT_REACTIVATED"]).count() == 2


@pytest.mark.parametrize("role", ["student", "lecturer", "administrator"])
def test_privileged_accounts_cannot_be_suspended(workflow, role):
    target = workflow[role]
    if role != "administrator":
        target.is_staff = True
        target.save(update_fields=["is_staff"])
    with pytest.raises(ValueError, match="Privileged"):
        change_account_availability(user=target, administrator=workflow["administrator"], action="suspend", reason="Example")


def test_suspension_cannot_bypass_pending_approval(workflow):
    student = workflow["student"]
    student.approval_status = "PENDING"
    student.save(update_fields=["approval_status"])
    with pytest.raises(ValueError, match="not eligible"):
        change_account_availability(user=student, administrator=workflow["administrator"], action="reactivate", reason="Example")


@pytest.mark.parametrize("role", ["student", "lecturer"])
@pytest.mark.parametrize("target", ["notice-detail", "notice-send", "notice-cancel", "support-review", "resource-edit", "resource-revision", "resource-disable", "account-suspend"])
def test_targeted_management_routes_are_restricted(client, workflow, role, target):
    notice = draft_notice(workflow)
    ticket = SupportRequest.objects.create(submitted_by=workflow["student"], subject="Example", message="Example")
    routes = {
        "notice-detail": reverse("core:notice_detail", args=[notice.pk]),
        "notice-send": reverse("core:notice_send", args=[notice.pk]),
        "notice-cancel": reverse("core:notice_cancel", args=[notice.pk]),
        "support-review": reverse("core:support_review", args=[ticket.pk]),
        "resource-edit": reverse("practicals:resource_edit", args=[workflow["approved_resource"].pk]),
        "resource-revision": reverse("practicals:resource_revision", args=[workflow["approved_resource"].pk]),
        "resource-disable": reverse("practicals:resource_availability", args=[workflow["approved_resource"].pk, "disable"]),
        "account-suspend": reverse("accounts:account_availability", args=[workflow["student"].pk, "suspend"]),
    }
    client.force_login(workflow[role])
    assert client.get(routes[target]).status_code == 403
    assert client.post(routes[target], {"confirm": "on", "reason": "Unauthorised"}).status_code == 403


def test_management_mutations_require_csrf(workflow):
    client = Client(enforce_csrf_checks=True)
    client.force_login(workflow["administrator"])
    notice = draft_notice(workflow)
    urls = [reverse("core:platform_settings"), reverse("core:notice_create"), reverse("core:notice_send", args=[notice.pk]), reverse("practicals:resource_availability", args=[workflow["approved_resource"].pk, "disable"]), reverse("accounts:account_availability", args=[workflow["student"].pk, "suspend"])]
    for url in urls:
        assert client.post(url, {"confirm": "on", "reason": "Example"}).status_code == 403
    assert not notice.deliveries.exists()
    workflow["student"].refresh_from_db()
    assert workflow["student"].is_platform_active


def test_disabled_resource_blocks_new_launch_and_submission_but_retains_evidence(workflow, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "evidence"
    resource = workflow["approved_resource"]
    task = PracticalTask.objects.create(offering=workflow["offering"], created_by=workflow["lecturer"], title="Resource disabling regression", instructions="Example", question="Example", evidence_requirements="CSV", due_at=timezone.now() + timedelta(days=7), max_score=100, status="PUBLISHED")
    task.resources.add(resource)
    submission = start_submission(task=task, student=workflow["student"])
    submission.resource = resource
    submission.response_text = "Synthetic response"
    submission.save()
    evidence = add_evidence(submission=submission, student=workflow["student"], uploaded_file=SimpleUploadedFile("example.csv", b"parameter,value\nspeed,30\n", content_type="text/csv"))
    change_resource_availability(resource=resource, administrator=workflow["administrator"], action="disable", reason="Maintenance")
    with pytest.raises(ValueError, match="not currently approved"):
        create_integration_launch(submission=submission, student=workflow["student"], callback_url="https://platform.example/practicals/integrations/return/", completion_url="https://platform.example/practicals/integrations/sessions/")
    with pytest.raises(ValueError, match="no longer approved"):
        formally_submit(submission=submission, student=workflow["student"])
    assert task.resources.filter(pk=resource.pk).exists()
    assert submission.evidence_files.filter(pk=evidence.pk).exists()
    assert evidence.file.storage.exists(evidence.file.name)
