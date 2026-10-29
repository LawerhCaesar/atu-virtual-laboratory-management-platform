def notification_summary(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "unread_notification_count": request.user.notifications.filter(read_at__isnull=True).count()
    }


def simulation_walkthrough(request):
    """Registered simulations receive the shared guide without template duplication."""
    if not request.user.is_authenticated or not request.user.is_platform_active:
        return {}
    match = getattr(request, "resolver_match", None)
    route = getattr(match, "view_name", None)
    if not route:
        return {}
    from .laboratory import SYSTEM_MODELS
    from .vehicle_baseline import VEHICLE_BASELINE
    from .module_students import student_profile

    for models in SYSTEM_MODELS.values():
        for model in models:
            if model["route_name"] == route:
                return {"walkthrough_module": {"route": route, "name": model["title"], "user_id": str(request.user.pk)},
                        "vehicle_baseline": VEHICLE_BASELINE,
                        "module_student": student_profile(route, model["title"])}
    return {}
