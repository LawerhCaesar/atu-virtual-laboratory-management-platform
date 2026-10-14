import secrets
import string

from django.db import transaction
from django.utils import timezone

from apps.auditlog.services import record_event

from .models import User


@transaction.atomic
def approve_for_academic_setup(*, user, reviewer):
    if user.role == User.Role.ADMINISTRATOR:
        raise ValueError("Administrator accounts cannot enter public approval workflow.")
    if user.approval_status != User.ApprovalStatus.PENDING:
        raise ValueError("Only pending accounts can be approved.")
    user.approval_status = User.ApprovalStatus.ACADEMIC_SETUP
    user.reviewed_by = reviewer
    user.reviewed_at = timezone.now()
    user.save(update_fields=["approval_status", "reviewed_by", "reviewed_at"])
    record_event(
        actor=reviewer,
        action="ACCOUNT_APPROVED",
        target=user,
        metadata={"next_status": User.ApprovalStatus.ACADEMIC_SETUP},
    )
    return user


@transaction.atomic
def reject_registration(*, user, reviewer):
    if user.approval_status != User.ApprovalStatus.PENDING:
        raise ValueError("Only pending accounts can be rejected.")
    user.approval_status = User.ApprovalStatus.REJECTED
    user.reviewed_by = reviewer
    user.reviewed_at = timezone.now()
    user.save(update_fields=["approval_status", "reviewed_by", "reviewed_at"])
    record_event(actor=reviewer, action="ACCOUNT_REJECTED", target=user)
    return user


def _temporary_password():
    random_part = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(14))
    return f"A7!{random_part}z"


@transaction.atomic
def reset_account_password(*, user, administrator):
    if user.role == User.Role.ADMINISTRATOR:
        raise ValueError("Use the authenticated password-change workflow for Administrator accounts.")
    temporary_password = _temporary_password()
    user.set_password(temporary_password)
    user.must_change_password = True
    user.save(update_fields=["password", "must_change_password"])
    record_event(
        actor=administrator,
        action="PASSWORD_RESET_BY_ADMIN",
        target=user,
        metadata={"role": user.role},
    )
    return temporary_password


@transaction.atomic
def change_account_availability(*, user, administrator, action, reason):
    if not administrator.is_platform_active or administrator.role != User.Role.ADMINISTRATOR:
        raise ValueError("An active Administrator is required.")
    user = User.objects.select_for_update().get(pk=user.pk)
    if user.role == User.Role.ADMINISTRATOR or user.is_staff or user.is_superuser or user.pk == administrator.pk:
        raise ValueError("Privileged accounts cannot be changed through this workflow.")
    if not reason.strip() or len(reason) > 500:
        raise ValueError("Provide a reason of no more than 500 characters.")
    if action == "suspend" and user.is_platform_active:
        user.approval_status = User.ApprovalStatus.SUSPENDED
        user.is_active = False
        event = "ACCOUNT_SUSPENDED"
    elif action == "reactivate" and user.approval_status == User.ApprovalStatus.SUSPENDED:
        if not hasattr(user, "academic_profile"):
            raise ValueError("Academic setup is required before reactivation.")
        user.approval_status = User.ApprovalStatus.ACTIVE
        user.is_active = True
        event = "ACCOUNT_REACTIVATED"
    else:
        raise ValueError("The account state has changed or is not eligible. Refresh before continuing.")
    user.session_revision += 1
    user.reviewed_by = administrator
    user.reviewed_at = timezone.now()
    user.save(update_fields=["approval_status", "is_active", "session_revision", "reviewed_by", "reviewed_at"])
    record_event(actor=administrator, action=event, target=user, metadata={"reason": reason.strip(), "role": user.role})
    return user
