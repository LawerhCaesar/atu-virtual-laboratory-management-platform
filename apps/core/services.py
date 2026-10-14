from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from apps.auditlog.services import record_event
from .models import AdministratorNotice, Notification


def require_administrator(user):
    if not user.is_platform_active or user.role != User.Role.ADMINISTRATOR:
        raise ValueError("An active Administrator is required.")


def notice_recipients(notice):
    recipients = User.objects.filter(is_active=True, approval_status=User.ApprovalStatus.ACTIVE, role__in=[User.Role.STUDENT, User.Role.LECTURER])
    if notice.audience == AdministratorNotice.Audience.INDIVIDUAL:
        return recipients.filter(pk=notice.recipient_id)
    if notice.audience != AdministratorNotice.Audience.ALL:
        return recipients.filter(role=notice.audience)
    return recipients


@transaction.atomic
def send_notice(*, notice, administrator):
    require_administrator(administrator)
    notice = AdministratorNotice.objects.select_for_update().get(pk=notice.pk)
    if notice.sent_at or notice.cancelled_at:
        raise ValueError("Only an unsent, uncancelled draft can be sent.")
    notice.full_clean()
    recipients = list(notice_recipients(notice))
    if not recipients:
        raise ValueError("No active recipients match this notice. Nothing was sent.")
    for recipient in recipients:
        notification = Notification(recipient=recipient, category=Notification.Category.SYSTEM, title=notice.title, message=notice.message, link=notice.link, notice=notice)
        notification.full_clean()
        notification.save()
    notice.sent_at = timezone.now()
    notice.save(update_fields=["sent_at"])
    record_event(actor=administrator, action="ADMIN_NOTICE_SENT", target=notice, metadata={"audience": notice.audience, "recipient_count": len(recipients)})
    return len(recipients)


@transaction.atomic
def cancel_notice(*, notice, administrator):
    require_administrator(administrator)
    notice = AdministratorNotice.objects.select_for_update().get(pk=notice.pk)
    if notice.sent_at or notice.cancelled_at:
        raise ValueError("Only an unsent draft can be cancelled. Sent notices are retained.")
    notice.cancelled_at = timezone.now()
    notice.save(update_fields=["cancelled_at"])
    record_event(actor=administrator, action="ADMIN_NOTICE_CANCELLED", target=notice)


def notify(*, recipient, category, title, message, link=""):
    notification = Notification(
        recipient=recipient,
        category=category,
        title=title,
        message=message,
        link=link,
    )
    notification.full_clean()
    notification.save()
    return notification
