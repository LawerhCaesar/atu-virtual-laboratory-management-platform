def notification_summary(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "unread_notification_count": request.user.notifications.filter(read_at__isnull=True).count()
    }
