from django.db import transaction

from apps.accounts.models import User
from apps.auditlog.services import record_event

from .models import Enrollment, TeachingAssignment


@transaction.atomic
def complete_academic_setup(*, user, configured_by, profile_form):
    if user.approval_status != User.ApprovalStatus.ACADEMIC_SETUP:
        raise ValueError("The account is not awaiting academic setup.")
    profile = profile_form.save(commit=False)
    profile.user = user
    profile.configured_by = configured_by
    profile.full_clean()
    profile.save()
    user.approval_status = User.ApprovalStatus.ACTIVE
    user.save(update_fields=["approval_status"])
    record_event(
        actor=configured_by,
        action="ACADEMIC_SETUP_COMPLETED",
        target=user,
        metadata={"profile_id": profile.pk},
    )
    return profile


@transaction.atomic
def update_offering_access(*, offering, administrator, lecturers, students):
    desired_lecturer_ids = {user.pk for user in lecturers}
    desired_student_ids = {user.pk for user in students}

    for assignment in offering.teaching_assignments.select_for_update():
        should_be_active = assignment.lecturer_id in desired_lecturer_ids
        if assignment.is_active != should_be_active:
            assignment.is_active = should_be_active
            assignment.save(update_fields=["is_active"])
        desired_lecturer_ids.discard(assignment.lecturer_id)
    for lecturer_id in desired_lecturer_ids:
        assignment = TeachingAssignment(
            offering=offering,
            lecturer_id=lecturer_id,
            assigned_by=administrator,
        )
        assignment.full_clean()
        assignment.save()

    for enrollment in offering.enrollments.select_for_update():
        should_be_active = enrollment.student_id in desired_student_ids
        if enrollment.is_active != should_be_active:
            enrollment.is_active = should_be_active
            enrollment.save(update_fields=["is_active"])
        desired_student_ids.discard(enrollment.student_id)
    for student_id in desired_student_ids:
        enrollment = Enrollment(
            offering=offering,
            student_id=student_id,
            enrolled_by=administrator,
        )
        enrollment.full_clean()
        enrollment.save()

    record_event(
        actor=administrator,
        action="COURSE_ACCESS_UPDATED",
        target=offering,
        metadata={
            "active_lecturer_ids": list(
                offering.teaching_assignments.filter(is_active=True).values_list(
                    "lecturer_id", flat=True
                )
            ),
            "active_student_ids": list(
                offering.enrollments.filter(is_active=True).values_list(
                    "student_id", flat=True
                )
            ),
        },
    )
