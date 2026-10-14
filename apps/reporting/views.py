from django.conf import settings
from django.db.models import Q
from django.shortcuts import render

from apps.accounts.decorators import administrator_required
from apps.auditlog.models import AuditEvent
from apps.auditlog.services import record_event
from apps.practicals.models import PracticalSubmission

from .forms import AuditFilterForm, SubmissionReportFilterForm
from .services import (
    audit_csv_response,
    filter_submissions,
    platform_metrics,
    submissions_csv_response,
    summary_pdf_response,
    users_csv_response,
)


def _submission_queryset():
    return PracticalSubmission.objects.select_related(
        "student", "task__offering__course", "resource", "assessment"
    )


@administrator_required
def report_dashboard(request):
    form = SubmissionReportFilterForm(request.GET or None)
    submissions = _submission_queryset()
    if form.is_valid():
        submissions = filter_submissions(submissions, form.cleaned_data)
    metrics = platform_metrics()
    return render(
        request,
        "reporting/dashboard.html",
        {
            "metrics": metrics,
            "metric_rows": [(label.replace("_", " ").title(), value) for label, value in metrics.items()],
            "form": form,
            "submissions": submissions[:100],
        },
    )


@administrator_required
def users_csv(request):
    record_event(actor=request.user, action="USERS_CSV_EXPORTED", request=request)
    return users_csv_response()


@administrator_required
def submissions_csv(request):
    form = SubmissionReportFilterForm(request.GET or None)
    submissions = _submission_queryset()
    if form.is_valid():
        submissions = filter_submissions(submissions, form.cleaned_data)
    record_event(actor=request.user, action="SUBMISSIONS_CSV_EXPORTED", request=request)
    return submissions_csv_response(submissions)


@administrator_required
def summary_pdf(request):
    record_event(actor=request.user, action="ADMINISTRATIVE_PDF_EXPORTED", request=request)
    return summary_pdf_response(development_label=settings.DEBUG)


def _audit_queryset(cleaned=None):
    events = AuditEvent.objects.select_related("actor")
    if not cleaned:
        return events
    if cleaned.get("q"):
        query = cleaned["q"]
        events = events.filter(
            Q(actor__full_name__icontains=query)
            | Q(actor__email__icontains=query)
            | Q(target_id__icontains=query)
            | Q(target_type__icontains=query)
        )
    if cleaned.get("action"):
        events = events.filter(action=cleaned["action"])
    if cleaned.get("date_from"):
        events = events.filter(created_at__date__gte=cleaned["date_from"])
    if cleaned.get("date_to"):
        events = events.filter(created_at__date__lte=cleaned["date_to"])
    return events


@administrator_required
def audit_report(request):
    actions = AuditEvent.objects.order_by().values_list("action", flat=True).distinct()
    form = AuditFilterForm(request.GET or None, actions=actions)
    events = _audit_queryset(form.cleaned_data if form.is_valid() else None)
    return render(request, "reporting/audit.html", {"form": form, "events": events[:250]})


@administrator_required
def audit_csv(request):
    actions = AuditEvent.objects.order_by().values_list("action", flat=True).distinct()
    form = AuditFilterForm(request.GET or None, actions=actions)
    events = _audit_queryset(form.cleaned_data if form.is_valid() else None)
    record_event(actor=request.user, action="AUDIT_CSV_EXPORTED", request=request)
    return audit_csv_response(events)
