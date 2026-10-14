from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.accounts.decorators import administrator_required
from apps.auditlog.services import record_event
from apps.academics.models import CourseOffering
from apps.practicals.models import ApprovedResource, Assessment, PracticalSubmission, PracticalTask

from .forms import AdministratorNoticeForm, PlatformSettingsForm, SupportRequestForm, SupportResponseForm
from .models import AdministratorNotice, Notification, PlatformSettings, SupportRequest, is_internal_link
from .services import cancel_notice, notice_recipients, notify, send_notice


def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    if not request.user.is_platform_active:
        raise PermissionDenied
    context = {}
    if request.user.role == User.Role.ADMINISTRATOR:
        context["pending_count"] = User.objects.filter(
            approval_status=User.ApprovalStatus.PENDING
        ).count()
        context["offering_count"] = CourseOffering.objects.filter(is_active=True).count()
        context["resource_review_count"] = ApprovedResource.objects.filter(
            status=ApprovedResource.Status.DRAFT
        ).count()
        template = "core/dashboard_admin.html"
    elif request.user.role == User.Role.LECTURER:
        context["assigned_offering_count"] = CourseOffering.objects.filter(
            teaching_assignments__lecturer=request.user,
            teaching_assignments__is_active=True,
            is_active=True,
        ).distinct().count()
        context["task_count"] = PracticalTask.objects.filter(created_by=request.user).count()
        context["review_count"] = PracticalSubmission.objects.filter(
            task__created_by=request.user,
            status__in=[
                PracticalSubmission.Status.SUBMITTED,
                PracticalSubmission.Status.RESUBMITTED,
            ],
        ).count()
        template = "core/dashboard_lecturer.html"
    elif request.user.role == User.Role.STUDENT:
        context["assigned_task_count"] = PracticalTask.objects.filter(
            status=PracticalTask.Status.PUBLISHED,
            offering__enrollments__student=request.user,
            offering__enrollments__is_active=True,
        ).distinct().count()
        context["submission_count"] = PracticalSubmission.objects.filter(
            student=request.user
        ).exclude(status=PracticalSubmission.Status.DRAFT).count()
        context["released_result_count"] = Assessment.objects.filter(
            submission__student=request.user,
            status=Assessment.Status.RELEASED,
        ).count()
        template = "core/dashboard_student.html"
    else:
        raise PermissionDenied
    return render(request, template, context)


@login_required
def notification_list(request):
    if not request.user.is_platform_active:
        raise PermissionDenied
    notifications = request.user.notifications.all()
    return render(request, "core/notification_list.html", {"notifications": notifications})


@login_required
def notification_open(request, notification_id):
    if not request.user.is_platform_active:
        raise PermissionDenied
    notification = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect(notification.link if notification.link and is_internal_link(notification.link) else "core:dashboard")


@administrator_required
def platform_settings(request):
    with transaction.atomic():
        current = PlatformSettings.objects.select_for_update().filter(pk=1).first() or PlatformSettings()
        form = PlatformSettingsForm(request.POST if request.method == "POST" else None, instance=current)
        if request.method == "POST" and form.is_valid():
            current = form.save(commit=False)
            current.updated_by = request.user
            current.full_clean()
            current.save()
            record_event(actor=request.user, action="PLATFORM_SETTINGS_UPDATED", target=current)
            messages.success(request, "Support settings updated.")
            return redirect("core:platform_settings")
    return render(request, "core/settings_form.html", {"form": form, "settings_record": current})


@administrator_required
def notice_management(request):
    notices = AdministratorNotice.objects.select_related("created_by", "recipient").annotate(delivery_count=Count("deliveries"), read_count=Count("deliveries", filter=Q(deliveries__read_at__isnull=False))).order_by("-created_at", "-pk")
    return render(request, "core/notice_management.html", {"notices": Paginator(notices, 25).get_page(request.GET.get("page"))})


@administrator_required
def notice_create(request):
    form = AdministratorNoticeForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.full_clean()
            notice.save()
            record_event(actor=request.user, action="ADMIN_NOTICE_DRAFTED", target=notice)
        return redirect("core:notice_detail", notice_id=notice.pk)
    return render(request, "core/notice_form.html", {"form": form})


@administrator_required
def notice_detail(request, notice_id):
    notice = get_object_or_404(AdministratorNotice.objects.select_related("recipient", "created_by"), pk=notice_id)
    return render(request, "core/notice_detail.html", {"notice": notice, "recipient_count": notice_recipients(notice).count(), "delivery_count": notice.deliveries.count(), "read_count": notice.deliveries.filter(read_at__isnull=False).count()})


@administrator_required
@require_POST
def notice_send(request, notice_id):
    notice = get_object_or_404(AdministratorNotice, pk=notice_id)
    try:
        count = send_notice(notice=notice, administrator=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Notice sent to {count} active accounts.")
    return redirect("core:notice_detail", notice_id=notice.pk)


@administrator_required
@require_POST
def notice_cancel(request, notice_id):
    notice = get_object_or_404(AdministratorNotice, pk=notice_id)
    try:
        cancel_notice(notice=notice, administrator=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Draft cancelled. Its record is retained.")
    return redirect("core:notice_detail", notice_id=notice.pk)


def help_page(request):
    context = {"support_settings": PlatformSettings.objects.filter(pk=1).first()}
    if request.user.is_authenticated and request.user.is_platform_active:
        context["support_requests"] = request.user.support_requests.all()[:25]
        form = SupportRequestForm(request.POST if request.method == "POST" else None)
        context["form"] = form
        if request.method == "POST" and form.is_valid():
            with transaction.atomic():
                ticket = form.save(commit=False)
                ticket.submitted_by = request.user
                ticket.save()
                record_event(actor=request.user, action="SUPPORT_REQUEST_CREATED", target=ticket)
            messages.success(request, "Your support request has been recorded.")
            return redirect("core:help")
    elif request.method == "POST":
        raise PermissionDenied
    return render(request, "core/help.html", context)


@administrator_required
def support_management(request):
    tickets = SupportRequest.objects.select_related("submitted_by", "reviewed_by")
    status = request.GET.get("status", "OPEN")
    if status in SupportRequest.Status.values:
        tickets = tickets.filter(status=status)
    return render(request, "core/support_management.html", {"tickets": Paginator(tickets, 25).get_page(request.GET.get("page")), "status": status})


@administrator_required
def support_review(request, ticket_id):
    with transaction.atomic():
        ticket = get_object_or_404(SupportRequest.objects.select_for_update().select_related("submitted_by"), pk=ticket_id)
        form = SupportResponseForm(request.POST if request.method == "POST" else None, instance=ticket)
        if request.method == "POST" and form.is_valid():
            ticket = form.save(commit=False)
            ticket.reviewed_by = request.user
            ticket.reviewed_at = timezone.now()
            ticket.save()
            notify(recipient=ticket.submitted_by, category=Notification.Category.SYSTEM, title=f"Support update: {ticket.subject}"[:180], message="An Administrator has responded to your platform support request. Open Help to read the response.", link=reverse("core:help"))
            record_event(actor=request.user, action="SUPPORT_REQUEST_REVIEWED", target=ticket, metadata={"status": ticket.status})
            messages.success(request, "Response saved and the account holder notified.")
            return redirect("core:support_management")
    return render(request, "core/support_review.html", {"ticket": ticket, "form": form})
