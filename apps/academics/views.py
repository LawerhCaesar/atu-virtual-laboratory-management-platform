from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import administrator_required
from apps.accounts.models import User
from apps.auditlog.services import record_event

from .forms import AcademicSetupForm, CourseForm, CourseOfferingForm, OfferingAccessForm
from .models import Course, CourseOffering
from .services import complete_academic_setup, update_offering_access


@administrator_required
def academic_setup(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.approval_status != User.ApprovalStatus.ACADEMIC_SETUP:
        messages.error(request, "That account is not awaiting academic setup.")
        return redirect("accounts:pending_approvals")
    form = AcademicSetupForm(request.POST or None, user=user)
    if request.method == "POST" and form.is_valid():
        try:
            complete_academic_setup(user=user, configured_by=request.user, profile_form=form)
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"{user.full_name}'s account is now active.")
            return redirect("accounts:pending_approvals")
    return render(request, "academics/setup.html", {"form": form, "account": user})


@administrator_required
def course_list(request):
    courses = Course.objects.select_related("department").all()
    return render(request, "academics/course_list.html", {"courses": courses})


@administrator_required
def course_create(request):
    form = CourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        course = form.save()
        record_event(actor=request.user, action="COURSE_CREATED", target=course)
        messages.success(request, f"{course.code} was created.")
        return redirect("academics:course_list")
    return render(request, "academics/course_form.html", {"form": form})


@administrator_required
def offering_list(request):
    offerings = CourseOffering.objects.select_related(
        "course", "programme", "academic_year"
    ).annotate(
        active_lecturer_count=Count(
            "teaching_assignments",
            filter=Q(teaching_assignments__is_active=True),
            distinct=True,
        ),
        active_student_count=Count(
            "enrollments",
            filter=Q(enrollments__is_active=True),
            distinct=True,
        ),
    )
    return render(request, "academics/offering_list.html", {"offerings": offerings})


@administrator_required
def offering_create(request):
    form = CourseOfferingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        offering = form.save(commit=False)
        offering.full_clean()
        offering.save()
        record_event(actor=request.user, action="COURSE_OFFERING_CREATED", target=offering)
        messages.success(request, "Course offering created. Assign access next.")
        return redirect("academics:offering_access", offering_id=offering.pk)
    return render(request, "academics/offering_form.html", {"form": form})


@administrator_required
def offering_access(request, offering_id):
    offering = get_object_or_404(
        CourseOffering.objects.select_related("course", "programme", "programme__department"),
        pk=offering_id,
    )
    form = OfferingAccessForm(request.POST or None, offering=offering)
    if request.method == "POST" and form.is_valid():
        update_offering_access(
            offering=offering,
            administrator=request.user,
            lecturers=form.cleaned_data["lecturers"],
            students=form.cleaned_data["students"],
        )
        messages.success(request, "Course access was updated.")
        return redirect("academics:offering_list")
    return render(request, "academics/offering_access.html", {"form": form, "offering": offering})
