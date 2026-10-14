from pathlib import Path

from django import forms
from django.conf import settings

from apps.academics.models import CourseOffering

from .models import ApprovedResource, Assessment, PracticalSubmission, PracticalTask


class ApprovedResourceForm(forms.ModelForm):
    url = forms.URLField(
        assume_scheme="https",
        help_text="Controlled link to the approved demonstration resource.",
    )
    integration_mode = forms.ChoiceField(
        choices=ApprovedResource.IntegrationMode.choices,
        required=False,
        initial=ApprovedResource.IntegrationMode.LINK_ONLY,
    )

    class Meta:
        model = ApprovedResource
        fields = (
            "title",
            "description",
            "url",
            "version_label",
            "integration_mode",
            "integration_key_id",
        )

    def clean_integration_mode(self):
        return self.cleaned_data.get("integration_mode") or ApprovedResource.IntegrationMode.LINK_ONLY


class ResourceAvailabilityForm(forms.Form):
    reason = forms.CharField(max_length=500, widget=forms.Textarea, help_text="Record the administrative reason; do not include passwords or private evidence.")
    confirm = forms.BooleanField(label="I understand that disabling blocks future use and pending signed returns, while existing records are retained.")


class PracticalTaskForm(forms.ModelForm):
    due_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = PracticalTask
        fields = (
            "offering",
            "title",
            "instructions",
            "question",
            "evidence_requirements",
            "due_at",
            "max_score",
            "max_resubmissions",
            "resources",
        )
        widgets = {"resources": forms.CheckboxSelectMultiple}

    def __init__(self, *args, lecturer, **kwargs):
        super().__init__(*args, **kwargs)
        self.lecturer = lecturer
        self.fields["offering"].queryset = CourseOffering.objects.filter(
            is_active=True,
            teaching_assignments__lecturer=lecturer,
            teaching_assignments__is_active=True,
        ).select_related("course", "academic_year").distinct()
        self.fields["resources"].queryset = ApprovedResource.objects.filter(
            status=ApprovedResource.Status.APPROVED
        )

    def clean_offering(self):
        offering = self.cleaned_data["offering"]
        if not offering.teaching_assignments.filter(
            lecturer=self.lecturer, is_active=True
        ).exists():
            raise forms.ValidationError("You are not assigned to this course offering.")
        return offering


class SubmissionForm(forms.ModelForm):
    run_started_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    run_completed_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = PracticalSubmission
        fields = (
            "response_text",
            "resource",
            "parameter_summary",
            "run_session_id",
            "run_started_at",
            "run_completed_at",
            "run_status",
            "output_summary",
        )

    def __init__(self, *args, task, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resource"].queryset = task.resources.filter(
            status=ApprovedResource.Status.APPROVED
        )
        self.fields["resource"].required = False


class EvidenceUploadForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={"accept": ".pdf,.png,.jpg,.jpeg,.csv,.txt"}
        ),
        help_text="PDF, PNG, JPEG, CSV or TXT; maximum 20 MB per file and 100 MB per submission."
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        extension = Path(uploaded.name).suffix.lower()
        if extension not in settings.EVIDENCE_ALLOWED_EXTENSIONS:
            raise forms.ValidationError("Upload a PDF, PNG, JPEG, CSV or TXT file.")
        if uploaded.size > settings.EVIDENCE_FILE_MAX_BYTES:
            raise forms.ValidationError("An evidence file cannot exceed 20 MB.")
        content_type = getattr(uploaded, "content_type", "")
        if content_type and content_type not in settings.EVIDENCE_ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError("The uploaded content type is not permitted.")
        header = uploaded.read(4096)
        uploaded.seek(0)
        signatures = {
            ".pdf": header.startswith(b"%PDF-"),
            ".png": header.startswith(b"\x89PNG\r\n\x1a\n"),
            ".jpg": header.startswith(b"\xff\xd8\xff"),
            ".jpeg": header.startswith(b"\xff\xd8\xff"),
        }
        if extension in signatures and not signatures[extension]:
            raise forms.ValidationError("The file content does not match its extension.")
        if extension in {".csv", ".txt"}:
            try:
                header.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise forms.ValidationError("Text evidence must use UTF-8 encoding.") from exc
        return uploaded


class AssessmentForm(forms.ModelForm):
    score = forms.DecimalField(min_value=0)

    class Meta:
        model = Assessment
        fields = ("score", "feedback")

    def __init__(self, *args, submission, **kwargs):
        super().__init__(*args, **kwargs)
        self.submission = submission
        self.fields["score"].widget.attrs["max"] = submission.task.max_score
        self.fields["score"].help_text = f"Maximum score: {submission.task.max_score}."

    def clean_score(self):
        score = self.cleaned_data.get("score")
        if score is not None and score > self.submission.task.max_score:
            raise forms.ValidationError("The score cannot exceed the task maximum.")
        return score


class ReturnForResubmissionForm(forms.Form):
    feedback = forms.CharField(
        label="Correction feedback",
        widget=forms.Textarea(attrs={"id": "id_correction_feedback"}),
        help_text="Explain what the student must correct before resubmitting.",
    )
