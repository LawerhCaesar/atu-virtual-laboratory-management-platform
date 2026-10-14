import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.academics.models import CourseOffering


def evidence_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"evidence/task-{instance.submission.task_id}/student-{instance.submission.student_id}/{uuid.uuid4().hex}{extension}"


class ApprovedResource(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        ARCHIVED = "ARCHIVED", "Archived"

    class IntegrationMode(models.TextChoices):
        LINK_ONLY = "LINK_ONLY", "Controlled link only"
        SIGNED_RETURN = "SIGNED_RETURN", "Signed JSON return"

    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    url = models.URLField(help_text="Controlled link to the approved demonstration resource.")
    version_label = models.CharField(max_length=50, blank=True)
    integration_mode = models.CharField(
        max_length=20,
        choices=IntegrationMode.choices,
        default=IntegrationMode.LINK_ONLY,
    )
    integration_key_id = models.SlugField(
        max_length=80,
        blank=True,
        help_text="Identifier for a shared secret configured outside the database.",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_resources",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_resources",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revision_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="revisions")

    class Meta:
        ordering = ["title", "version_label"]

    def clean(self):
        errors = {}
        if not settings.DEBUG and self.url and not self.url.startswith("https://"):
            errors["url"] = "Production demonstration resources must use HTTPS."
        if self.created_by_id and self.created_by.role != self.created_by.Role.ADMINISTRATOR:
            errors["created_by"] = "Only Administrators can register approved resources."
        if self.integration_mode == self.IntegrationMode.SIGNED_RETURN:
            if not self.integration_key_id:
                errors["integration_key_id"] = "A key identifier is required for signed JSON return."
            elif self.integration_key_id not in settings.INTEGRATION_SHARED_SECRETS:
                errors["integration_key_id"] = "No shared secret is configured for this key identifier."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        suffix = f" ({self.version_label})" if self.version_label else ""
        return f"{self.title}{suffix}"


class PracticalTask(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        CLOSED = "CLOSED", "Closed"
        ARCHIVED = "ARCHIVED", "Archived"

    offering = models.ForeignKey(CourseOffering, on_delete=models.PROTECT, related_name="practical_tasks")
    title = models.CharField(max_length=180)
    instructions = models.TextField()
    question = models.TextField()
    evidence_requirements = models.TextField(
        help_text="State the plots, metrics, files, screenshots or other evidence students must submit."
    )
    due_at = models.DateTimeField()
    max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    max_resubmissions = models.PositiveSmallIntegerField(default=1)
    resources = models.ManyToManyField(ApprovedResource, blank=True, related_name="practical_tasks")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_practical_tasks",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_at", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["offering", "title"],
                name="unique_practical_task_title_per_offering",
            )
        ]

    def clean(self):
        errors = {}
        if self.created_by_id and self.created_by.role != self.created_by.Role.LECTURER:
            errors["created_by"] = "Only Lecturers can create practical tasks."
        if self.status == self.Status.PUBLISHED and self.due_at and self.due_at <= timezone.now():
            errors["due_at"] = "A published task must have a future deadline."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.offering.course.code}: {self.title}"


class PracticalSubmission(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        RETURNED = "RETURNED", "Returned for resubmission"
        RESUBMITTED = "RESUBMITTED", "Resubmitted"
        ASSESSED = "ASSESSED", "Assessed"

    class RunStatus(models.TextChoices):
        NOT_RECORDED = "NOT_RECORDED", "Not recorded"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    task = models.ForeignKey(PracticalTask, on_delete=models.PROTECT, related_name="submissions")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="practical_submissions",
    )
    attempt_number = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    response_text = models.TextField(blank=True)
    resource = models.ForeignKey(
        ApprovedResource,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="submission_runs",
    )
    resource_version = models.CharField(max_length=50, blank=True)
    parameter_summary = models.TextField(blank=True)
    run_session_id = models.CharField(max_length=100, blank=True)
    run_started_at = models.DateTimeField(null=True, blank=True)
    run_completed_at = models.DateTimeField(null=True, blank=True)
    run_status = models.CharField(
        max_length=20,
        choices=RunStatus.choices,
        default=RunStatus.NOT_RECORDED,
    )
    output_summary = models.TextField(blank=True)
    integration_payload = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["task", "student", "attempt_number"],
                name="unique_submission_attempt",
            )
        ]

    def clean(self):
        errors = {}
        if self.student_id and self.student.role != self.student.Role.STUDENT:
            errors["student"] = "Only Student accounts can own submissions."
        if self.task_id and self.student_id and not self.task.offering.enrollments.filter(
            student=self.student, is_active=True
        ).exists():
            errors["student"] = "The student is not actively enrolled in this course offering."
        if self.resource_id and self.task_id and not self.task.resources.filter(pk=self.resource_id).exists():
            errors["resource"] = "Select a resource linked to this practical task."
        if self.run_started_at and self.run_completed_at and self.run_completed_at < self.run_started_at:
            errors["run_completed_at"] = "Run completion cannot be earlier than its start."
        if errors:
            raise ValidationError(errors)

    @property
    def can_edit(self):
        return self.status == self.Status.DRAFT

    def __str__(self):
        return f"{self.task} · {self.student} · attempt {self.attempt_number}"


class EvidenceFile(models.Model):
    submission = models.ForeignKey(
        PracticalSubmission,
        on_delete=models.CASCADE,
        related_name="evidence_files",
    )
    file = models.FileField(upload_to=evidence_upload_path, max_length=500)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveBigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at", "pk"]

    def clean(self):
        extension = Path(self.original_name).suffix.lower()
        if extension not in settings.EVIDENCE_ALLOWED_EXTENSIONS:
            raise ValidationError({"file": "Unsupported evidence file type."})
        if self.size_bytes > settings.EVIDENCE_FILE_MAX_BYTES:
            raise ValidationError({"file": "An evidence file cannot exceed 20 MB."})
        if self.content_type and self.content_type not in settings.EVIDENCE_ALLOWED_CONTENT_TYPES:
            raise ValidationError({"file": "The uploaded content type is not permitted."})

    def __str__(self):
        return self.original_name


class Assessment(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft assessment"
        RELEASED = "RELEASED", "Released"

    submission = models.OneToOneField(
        PracticalSubmission,
        on_delete=models.PROTECT,
        related_name="assessment",
    )
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="practical_assessments",
    )
    score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    feedback = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    assessed_at = models.DateTimeField(auto_now=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-assessed_at"]

    def clean(self):
        errors = {}
        if self.lecturer_id and self.lecturer.role != self.lecturer.Role.LECTURER:
            errors["lecturer"] = "Only Lecturers can assess submissions."
        if self.score is not None and self.submission_id:
            if self.score > self.submission.task.max_score:
                errors["score"] = "The score cannot exceed the task maximum."
        if self.status == self.Status.RELEASED and self.score is None:
            errors["score"] = "A score is required before result release."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Assessment for {self.submission}"


class IntegrationSession(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        LAUNCHED = "LAUNCHED", "Launched"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    submission = models.ForeignKey(
        PracticalSubmission,
        on_delete=models.PROTECT,
        related_name="integration_sessions",
    )
    resource = models.ForeignKey(
        ApprovedResource,
        on_delete=models.PROTECT,
        related_name="integration_sessions",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CREATED, db_index=True)
    launch_token_hash = models.CharField(max_length=64)
    request_payload = models.JSONField(default=dict)
    result_payload = models.JSONField(default=dict, blank=True)
    signature_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    launched_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        errors = {}
        if self.resource_id and self.resource.integration_mode != self.resource.IntegrationMode.SIGNED_RETURN:
            errors["resource"] = "This resource does not support signed result return."
        if self.resource_id and self.submission_id:
            if not self.submission.task.resources.filter(pk=self.resource_id).exists():
                errors["resource"] = "The resource is not linked to this practical task."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Integration session {self.public_id}"
