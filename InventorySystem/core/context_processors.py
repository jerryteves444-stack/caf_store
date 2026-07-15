def notifications_processor(request):
    """Injects unread notification count/list into every template so the
    navbar bell icon works without every view needing to fetch it."""
    if not request.user.is_authenticated:
        return {}
    from notifications.models import Notification
    qs = Notification.objects.filter(recipient=request.user, is_read=False).order_by("-created_at")
    return {
        "unread_notifications": qs[:8],
        "unread_notifications_count": qs.count(),
    }
