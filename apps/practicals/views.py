from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Prefetch
from django.db import transaction
from django.http import FileResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.accounts.decorators import administrator_required, lecturer_required, student_required
from apps.auditlog.services import record_event

from .forms import (
    ApprovedResourceForm,
    ResourceAvailabilityForm,
    AssessmentForm,
    EvidenceUploadForm,
    PracticalTaskForm,
    ReturnForResubmissionForm,
    SubmissionForm,
)
from .models import (
    ApprovedResource,
    Assessment,
    EvidenceFile,
    IntegrationSession,
    PracticalSubmission,
    PracticalTask,
)
from .services import (
    add_evidence,
    accept_integration_return,
    approve_resource,
    change_resource_availability,
    resource_has_history,
    update_resource,
    create_integration_launch,
    formally_submit,
    publish_task,
    release_result,
    remove_evidence,
    return_for_resubmission,
    save_assessment,
    start_submission,
    IntegrationAuthenticationError,
    IntegrationConflictError,
)


@administrator_required
def resource_list(request):
    resources = ApprovedResource.objects.select_related("created_by", "approved_by")
    return render(request, "practicals/resource_list.html", {"resources": resources})


@administrator_required
def resource_create(request):
    form = ApprovedResourceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        resource = form.save(commit=False)
        resource.created_by = request.user
        resource.full_clean()
        resource.save()
        record_event(actor=request.user, action="RESOURCE_REGISTERED", target=resource)
        messages.success(request, "Resource saved as a draft for approval.")
        return redirect("practicals:resource_list")
    return render(request, "practicals/resource_form.html", {"form": form})


@administrator_required
def resource_edit(request, resource_id):
    resource = get_object_or_404(ApprovedResource, pk=resource_id)
    if resource.status == ApprovedResource.Status.ARCHIVED or resource_has_history(resource):
        messages.error(request, "This resource cannot be edited in place. Restore an unused resource or create a new revision to preserve task/run history.")
        return redirect("practicals:resource_list")
    form = ApprovedResourceForm(request.POST if request.method == "POST" else None, instance=resource)
    if request.method == "POST" and form.is_valid():
        try:
            update_resource(resource=resource, administrator=request.user, changes=form.cleaned_data)
        except (ValueError, ValidationError) as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Resource updated and returned to draft. Approval is required again.")
            return redirect("practicals:resource_list")
    return render(request, "practicals/resource_form.html", {"form": form, "editing": True})


@administrator_required
def resource_revision(request, resource_id):
    original = get_object_or_404(ApprovedResource, pk=resource_id)
    initial = {name: getattr(original, name) for name in ApprovedResourceForm._meta.fields}
    initial["version_label"] = ""
    form = ApprovedResourceForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        if not form.cleaned_data["version_label"] or form.cleaned_data["version_label"] == original.version_label:
            form.add_error("version_label", "Use a new, non-empty version label for this revision.")
        else:
            with transaction.atomic():
                revision = form.save(commit=False)
                revision.created_by = request.user
                revision.revision_of = original
                revision.full_clean()
                revision.save()
                record_event(actor=request.user, action="RESOURCE_REVISION_CREATED", target=revision, metadata={"revision_of": original.pk})
            messages.success(request, "New revision saved as a draft. Existing tasks and runs remain linked to the original.")
            return redirect("practicals:resource_list")
    return render(request, "practicals/resource_form.html", {"form": form, "revision_of": original})


@administrator_required
def resource_availability(request, resource_id, action):
    resource = get_object_or_404(ApprovedResource, pk=resource_id)
    if action not in ["disable", "restore"]:
        raise PermissionDenied
    form = ResourceAvailabilityForm(request.POST if request.method == "POST" else None)
    if action == "restore":
        form.fields["confirm"].label = "I understand that restoration returns this resource to draft and requires fresh approval."
    if request.method == "POST" and form.is_valid():
        try:
            change_resource_availability(resource=resource, administrator=request.user, action=action, reason=form.cleaned_data["reason"])
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Resource disabled; records retained." if action == "disable" else "Resource restored to draft for review and approval.")
            return redirect("practicals:resource_list")
    return render(request, "practicals/resource_availability.html", {"resource": resource, "action": action, "form": form})


@administrator_required
def resource_approve(request, resource_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    resource = get_object_or_404(ApprovedResource, pk=resource_id)
    try:
        approve_resource(resource=resource, administrator=request.user)
    except (ValueError, ValidationError) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"{resource.title} is now approved.")
    return redirect("practicals:resource_list")


@lecturer_required
def lecturer_task_list(request):
    tasks = PracticalTask.objects.filter(created_by=request.user).select_related(
        "offering__course", "offering__academic_year"
    )
    return render(request, "practicals/lecturer_task_list.html", {"tasks": tasks})


@lecturer_required
def task_create(request):
    form = PracticalTaskForm(request.POST or None, lecturer=request.user)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.created_by = request.user
        task.full_clean()
        task.save()
        form.save_m2m()
        record_event(actor=request.user, action="PRACTICAL_TASK_CREATED", target=task)
        messages.success(request, "Practical task saved as a draft.")
        return redirect("practicals:lecturer_task_list")
    return render(request, "practicals/task_form.html", {"form": form, "editing": False})


@lecturer_required
def task_edit(request, task_id):
    task = get_object_or_404(PracticalTask, pk=task_id, created_by=request.user)
    if task.status != PracticalTask.Status.DRAFT:
        messages.error(request, "Only draft tasks can be edited.")
        return redirect("practicals:lecturer_task_list")
    form = PracticalTaskForm(request.POST or None, instance=task, lecturer=request.user)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.full_clean()
        task.save()
        form.save_m2m()
        record_event(actor=request.user, action="PRACTICAL_TASK_UPDATED", target=task)
        messages.success(request, "Draft task updated.")
        return redirect("practicals:lecturer_task_list")
    return render(request, "practicals/task_form.html", {"form": form, "editing": True})


@lecturer_required
def task_publish(request, task_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    task = get_object_or_404(PracticalTask, pk=task_id, created_by=request.user)
    try:
        publish_task(task=task, lecturer=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Practical task published to enrolled students.")
    return redirect("practicals:lecturer_task_list")


@student_required
def student_task_list(request):
    tasks = PracticalTask.objects.filter(
        status=PracticalTask.Status.PUBLISHED,
        offering__is_active=True,
        offering__enrollments__student=request.user,
        offering__enrollments__is_active=True,
    ).select_related("offering__course", "offering__academic_year").distinct()
    return render(request, "practicals/student_task_list.html", {"tasks": tasks})


@student_required
def student_task_detail(request, task_id):
    task = get_object_or_404(
        PracticalTask.objects.filter(
            status=PracticalTask.Status.PUBLISHED,
            offering__is_active=True,
            offering__enrollments__student=request.user,
            offering__enrollments__is_active=True,
        ).select_related("offering__course", "offering__academic_year").prefetch_related(
            Prefetch("resources", queryset=ApprovedResource.objects.filter(status=ApprovedResource.Status.APPROVED))
        ),
        pk=task_id,
    )
    submissions = task.submissions.filter(student=request.user).prefetch_related(
        "evidence_files", "assessment"
    ).order_by("-attempt_number")
    latest_submission = submissions.first()
    deadline_open = timezone.now() <= task.due_at
    can_start_submission = deadline_open and (
        latest_submission is None
        or (
            latest_submission.status == PracticalSubmission.Status.RETURNED
            and latest_submission.attempt_number < task.max_resubmissions + 1
        )
    )
    return render(
        request,
        "practicals/student_task_detail.html",
        {
            "task": task,
            "submissions": submissions,
            "latest_submission": latest_submission,
            "can_start_submission": can_start_submission,
            "deadline_open": deadline_open,
        },
    )


@student_required
def submission_start(request, task_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    task = get_object_or_404(
        PracticalTask.objects.filter(
            status=PracticalTask.Status.PUBLISHED,
            offering__enrollments__student=request.user,
            offering__enrollments__is_active=True,
        ),
        pk=task_id,
    )
    try:
        submission = start_submission(task=task, student=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("practicals:student_task_detail", task_id=task.pk)
    return redirect("practicals:submission_workspace", submission_id=submission.pk)


@student_required
def submission_workspace(request, submission_id):
    submission = get_object_or_404(
        PracticalSubmission.objects.select_related(
            "task__offering__course", "resource"
        ).prefetch_related("evidence_files"),
        pk=submission_id,
        student=request.user,
    )
    if not submission.can_edit:
        return redirect("practicals:student_task_detail", task_id=submission.task_id)
    form = SubmissionForm(request.POST or None, instance=submission, task=submission.task)
    if request.method == "POST" and form.is_valid():
        submission = form.save(commit=False)
        submission.full_clean()
        submission.save()
        record_event(actor=request.user, action="SUBMISSION_DRAFT_UPDATED", target=submission)
        messages.success(request, "Draft response saved.")
        return redirect("practicals:submission_workspace", submission_id=submission.pk)
    return render(
        request,
        "practicals/submission_workspace.html",
        {
            "submission": submission,
            "form": form,
            "evidence_form": EvidenceUploadForm(),
        },
    )


@student_required
def evidence_add(request, submission_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    submission = get_object_or_404(PracticalSubmission, pk=submission_id, student=request.user)
    form = EvidenceUploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            add_evidence(
                submission=submission,
                student=request.user,
                uploaded_file=form.cleaned_data["file"],
            )
        except (ValueError, ValidationError) as exc:
            messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
        else:
            messages.success(request, "Evidence file added to the draft.")
    else:
        messages.error(request, " ".join(form.errors.get("file", [])))
    return redirect("practicals:submission_workspace", submission_id=submission.pk)


@student_required
def evidence_remove(request, submission_id, evidence_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    evidence = get_object_or_404(
        EvidenceFile.objects.select_related("submission"),
        pk=evidence_id,
        submission_id=submission_id,
        submission__student=request.user,
    )
    try:
        remove_evidence(evidence=evidence, student=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Evidence file removed.")
    return redirect("practicals:submission_workspace", submission_id=submission_id)


@student_required
def submission_confirm(request, submission_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    submission = get_object_or_404(PracticalSubmission, pk=submission_id, student=request.user)
    try:
        formally_submit(submission=submission, student=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("practicals:submission_workspace", submission_id=submission.pk)
    messages.success(request, "Submission confirmed and sent to your lecturer.")
    return redirect("practicals:student_task_detail", task_id=submission.task_id)


@login_required
def evidence_download(request, evidence_id):
    if not request.user.is_platform_active:
        raise PermissionDenied
    evidence = get_object_or_404(
        EvidenceFile.objects.select_related(
            "submission__student", "submission__task__created_by", "submission__task__offering"
        ),
        pk=evidence_id,
    )
    allowed = request.user.role == request.user.Role.ADMINISTRATOR
    allowed = allowed or evidence.submission.student_id == request.user.pk
    if request.user.role == request.user.Role.LECTURER:
        allowed = allowed or (
            evidence.submission.task.created_by_id == request.user.pk
            and evidence.submission.task.offering.teaching_assignments.filter(
                lecturer=request.user, is_active=True
            ).exists()
        )
    if not allowed:
        raise PermissionDenied
    record_event(actor=request.user, action="EVIDENCE_DOWNLOADED", target=evidence, request=request)
    return FileResponse(
        evidence.file.open("rb"),
        as_attachment=True,
        filename=evidence.original_name,
        content_type=evidence.content_type or "application/octet-stream",
    )


@lecturer_required
def review_queue(request):
    submissions = PracticalSubmission.objects.filter(
        task__created_by=request.user,
    ).exclude(status=PracticalSubmission.Status.DRAFT).select_related(
        "task__offering__course", "student"
    )
    return render(request, "practicals/review_queue.html", {"submissions": submissions})


def _lecturer_submission(request, submission_id):
    return get_object_or_404(
        PracticalSubmission.objects.filter(task__created_by=request.user).select_related(
            "task__offering__course", "student", "resource"
        ).prefetch_related("evidence_files"),
        pk=submission_id,
    )


@lecturer_required
def submission_review(request, submission_id):
    submission = _lecturer_submission(request, submission_id)
    try:
        assessment = submission.assessment
    except Assessment.DoesNotExist:
        assessment = None
    assessment_form = AssessmentForm(instance=assessment, submission=submission)
    return_form = ReturnForResubmissionForm()
    return render(
        request,
        "practicals/submission_review.html",
        {
            "submission": submission,
            "assessment": assessment,
            "assessment_form": assessment_form,
            "return_form": return_form,
        },
    )


@lecturer_required
def assessment_save(request, submission_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    submission = _lecturer_submission(request, submission_id)
    try:
        existing = submission.assessment
    except Assessment.DoesNotExist:
        existing = None
    form = AssessmentForm(request.POST, instance=existing, submission=submission)
    if form.is_valid():
        try:
            save_assessment(
                submission=submission,
                lecturer=request.user,
                assessment_form=form,
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Assessment saved as a draft.")
    else:
        messages.error(request, "Correct the assessment errors and try again.")
        return render(
            request,
            "practicals/submission_review.html",
            {
                "submission": submission,
                "assessment": existing,
                "assessment_form": form,
                "return_form": ReturnForResubmissionForm(),
            },
        )
    return redirect("practicals:submission_review", submission_id=submission.pk)


@lecturer_required
def submission_return(request, submission_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    submission = _lecturer_submission(request, submission_id)
    form = ReturnForResubmissionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Feedback is required when requesting resubmission.")
    else:
        try:
            return_for_resubmission(
                submission=submission,
                lecturer=request.user,
                feedback=form.cleaned_data["feedback"],
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "The submission was returned for resubmission.")
    return redirect("practicals:submission_review", submission_id=submission.pk)


@lecturer_required
def result_release(request, assessment_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    assessment = get_object_or_404(
        Assessment.objects.filter(submission__task__created_by=request.user), pk=assessment_id
    )
    try:
        release_result(assessment=assessment, lecturer=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "The result is now visible to the student.")
    return redirect("practicals:submission_review", submission_id=assessment.submission_id)


@student_required
def result_list(request):
    assessments = Assessment.objects.filter(
        submission__student=request.user,
        status=Assessment.Status.RELEASED,
    ).select_related("submission__task__offering__course")
    return render(request, "practicals/result_list.html", {"assessments": assessments})


@student_required
def result_detail(request, assessment_id):
    assessment = get_object_or_404(
        Assessment.objects.filter(
            submission__student=request.user,
            status=Assessment.Status.RELEASED,
        ).select_related("submission__task__offering__course"),
        pk=assessment_id,
    )
    return render(request, "practicals/result_detail.html", {"assessment": assessment})


@student_required
def integration_launch(request, submission_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    submission = get_object_or_404(
        PracticalSubmission.objects.select_related("task", "resource"),
        pk=submission_id,
        student=request.user,
    )
    callback_url = request.build_absolute_uri(reverse("practicals:integration_return"))
    completion_base = request.build_absolute_uri("/practicals/integrations/sessions/")
    try:
        integration, launch_url = create_integration_launch(
            submission=submission,
            student=request.user,
            callback_url=callback_url,
            completion_url=completion_base,
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("practicals:submission_workspace", submission_id=submission.pk)
    return redirect(launch_url)


@student_required
def integration_status(request, public_id):
    integration = get_object_or_404(
        IntegrationSession.objects.select_related("resource", "submission__task"),
        public_id=public_id,
        submission__student=request.user,
    )
    return render(request, "practicals/integration_status.html", {"integration": integration})


@csrf_exempt
@require_POST
def integration_return(request):
    try:
        content_length = int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        return JsonResponse({"accepted": False, "error": "Invalid content length."}, status=400)
    if content_length > settings.INTEGRATION_CALLBACK_MAX_BYTES:
        return JsonResponse({"accepted": False, "error": "Payload too large."}, status=413)
    raw_body = request.body
    if len(raw_body) > settings.INTEGRATION_CALLBACK_MAX_BYTES:
        return JsonResponse({"accepted": False, "error": "Payload too large."}, status=413)
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return JsonResponse({"accepted": False, "error": "Invalid JSON."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"accepted": False, "error": "JSON object required."}, status=400)
    try:
        integration = accept_integration_return(
            raw_body=raw_body,
            payload=payload,
            signature=request.headers.get("X-ATU-Signature", ""),
        )
    except IntegrationAuthenticationError:
        return JsonResponse({"accepted": False, "error": "Authentication failed."}, status=403)
    except IntegrationConflictError as exc:
        return JsonResponse({"accepted": False, "error": str(exc)}, status=409)
    except IntegrationSession.DoesNotExist:
        return JsonResponse({"accepted": False, "error": "Session not found."}, status=404)
    except (ValueError, ValidationError) as exc:
        return JsonResponse({"accepted": False, "error": str(exc)}, status=400)
    return JsonResponse(
        {"accepted": True, "session_id": str(integration.public_id), "status": integration.status}
    )
import json

from django.conf import settings
