from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver


def _client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    from audit.models import AuditLog
    AuditLog.objects.create(
        user=user,
        action=AuditLog.Action.LOGIN,
        ip_address=_client_ip(request),
        new_value=f"{user.username} logged in",
    )


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    from audit.models import AuditLog
    if user is None:
        return
    AuditLog.objects.create(
        user=user,
        action=AuditLog.Action.LOGOUT,
        ip_address=_client_ip(request),
        new_value=f"{user.username} logged out",
    )


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    from audit.models import AuditLog
    AuditLog.objects.create(
        user=None,
        action=AuditLog.Action.LOGIN_FAILED,
        ip_address=_client_ip(request) if request else "0.0.0.0",
        new_value=f"Failed login attempt for '{credentials.get('username')}'",
    )
