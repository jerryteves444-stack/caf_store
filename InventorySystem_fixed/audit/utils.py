from .models import AuditLog


def _client_ip(request):
    if request is None:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(request, action, target=None, old_value="", new_value="", user=None):
    """Central helper used by mixins/services throughout the project so
    every important action produces one consistent AuditLog row."""
    actor = user or (getattr(request, "user", None) if request else None)
    if actor is not None and not getattr(actor, "is_authenticated", True):
        actor = None
    AuditLog.objects.create(
        user=actor,
        action=action,
        ip_address=_client_ip(request),
        target_repr=str(target) if target is not None else "",
        old_value=str(old_value),
        new_value=str(new_value),
    )
