from .models import AuditEvent


def _client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def record_event(*, action, actor=None, target=None, request=None, metadata=None):
    return AuditEvent.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        action=action,
        target_type=target._meta.label if target is not None else "",
        target_id=str(target.pk) if target is not None and target.pk is not None else "",
        ip_address=_client_ip(request),
        metadata=metadata or {},
    )

