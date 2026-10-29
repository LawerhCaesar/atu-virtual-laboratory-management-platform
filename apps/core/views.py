from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import DatabaseError, connection, transaction
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_safe

from apps.accounts.models import User
from apps.accounts.decorators import administrator_required
from apps.accounts.decorators import roles_required
from apps.auditlog.services import record_event
from apps.academics.models import CourseOffering
from apps.practicals.models import ApprovedResource, Assessment, PracticalSubmission, PracticalTask

from .forms import AdministratorNoticeForm, PlatformSettingsForm, SupportRequestForm, SupportResponseForm
from .models import AdministratorNotice, Notification, PlatformSettings, SupportRequest, is_internal_link
from .services import cancel_notice, notice_recipients, notify, send_notice
from .laboratory import ENGINE_MODEL_NAME, ENGINE_VIEW_KEYS, SYSTEM_MODELS, SYSTEMS
from .learning_facts import backup_fact, random_fact


def home(request):
    # Never make sign-in/page rendering wait for an external content provider.
    return render(request, "core/home.html", {"systems": SYSTEMS, "learning_fact": backup_fact()})


@never_cache
@require_safe
def learning_fact(request):
    excluded = request.GET.getlist("exclude")[-10:]
    excluded = [value[:100] for value in excluded]
    return JsonResponse(random_fact(excluded))


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def laboratory(request):
    return render(request, "core/laboratory.html", {"systems": [{**s, "model_count": len(SYSTEM_MODELS.get(s["slug"], ()))} for s in SYSTEMS]})


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def fuel_delivery(request):
    return render(request, "core/fuel_delivery.html")


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def brakelab(request):
    return render(request, "core/brakelab.html")


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def wheel_slip(request):
    return render(request, "core/wheel_slip.html")


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def steering_response(request):
    return render(request, "core/steering_response.html")


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def micro_hybrid(request):
    return render(request, "core/micro_hybrid.html")


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def laboratory_system(request, system_slug):
    system = next((item for item in SYSTEMS if item["slug"] == system_slug), None)
    if system is None:
        raise Http404("Unknown laboratory system")
    return render(request, "core/laboratory_system.html", {
        "system": system, "models": SYSTEM_MODELS.get(system_slug, ()),
    })


@never_cache
@require_safe
def readiness(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                return JsonResponse({"status": "unavailable"}, status=503)
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def engine_live_data(request):
    """Virtual engine live-data experiment in the ICE environment."""
    requested_view = request.GET.get("view", "overview")
    return render(request, "core/engine_live_data.html", {
        "initial_view": requested_view if requested_view in ENGINE_VIEW_KEYS else "overview",
        "model_name": ENGINE_MODEL_NAME,
    })


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


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def bless(request):
    return render(request, "core/bless.html")


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def battery_energy(request):
    return render(request, "core/battery_energy.html")


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def engine_generator(request):
    return render(request, "core/engine_generator.html")


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def ect(request):
    return render(request, "core/ect.html")


@roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def edward(request):
    return render(request, "core/edward.html")
