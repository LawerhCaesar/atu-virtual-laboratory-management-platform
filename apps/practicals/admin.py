from django.contrib import admin

from .models import (
    ApprovedResource,
    Assessment,
    EvidenceFile,
    IntegrationSession,
    PracticalSubmission,
    PracticalTask,
)


@admin.register(ApprovedResource)
class ApprovedResourceAdmin(admin.ModelAdmin):
    # Use audited platform workflows; the backend must not bypass history freezes.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = (
        "title",
        "version_label",
        "integration_mode",
        "integration_key_id",
        "status",
        "approved_by",
        "approved_at",
    )
    list_filter = ("status", "integration_mode")
    search_fields = ("title", "description")


@admin.register(PracticalTask)
class PracticalTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "offering", "created_by", "status", "due_at", "max_score")
    list_filter = ("status", "offering__academic_year", "offering__semester")
    search_fields = ("title", "question", "offering__course__code")


@admin.register(PracticalSubmission)
class PracticalSubmissionAdmin(admin.ModelAdmin):
    list_display = ("task", "student", "attempt_number", "status", "submitted_at")
    list_filter = ("status", "task__offering__academic_year")
    search_fields = ("student__email", "student__full_name", "task__title", "run_session_id")


@admin.register(EvidenceFile)
class EvidenceFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "submission", "size_bytes", "uploaded_at")
    search_fields = ("original_name", "submission__student__email")
    readonly_fields = ("file", "original_name", "content_type", "size_bytes", "uploaded_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("submission", "lecturer", "score", "status", "assessed_at", "released_at")
    list_filter = ("status",)
    search_fields = ("submission__student__email", "submission__task__title")


@admin.register(IntegrationSession)
class IntegrationSessionAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "submission",
        "resource",
        "status",
        "signature_verified",
        "launched_at",
        "returned_at",
    )
    list_filter = ("status", "signature_verified", "resource")
    search_fields = ("public_id", "submission__student__email", "submission__task__title")
    readonly_fields = (
        "public_id",
        "submission",
        "resource",
        "status",
        "launch_token_hash",
        "request_payload",
        "result_payload",
        "signature_verified",
        "created_at",
        "launched_at",
        "returned_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
