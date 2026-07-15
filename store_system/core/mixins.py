"""
Reusable Role-Based Access Control (RBAC) mixins for Class-Based Views.

Usage:
    class ProductCreateView(RoleRequiredMixin, CreateView):
        allowed_roles = ["ADMIN", "INVENTORY_STAFF"]
        ...
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restricts a view to users whose `role` is in `allowed_roles`.

    Superusers always pass. If `allowed_roles` is left empty, any
    authenticated user is allowed (the view is simply login-gated).
    """

    allowed_roles = []
    raise_exception = False

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not self.allowed_roles:
            return True
        return getattr(user, "role", None) in self.allowed_roles

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You do not have permission to perform this action.")
        return super().handle_no_permission()


class AdminOnlyMixin(RoleRequiredMixin):
    allowed_roles = ["ADMIN"]


class ManagerUpMixin(RoleRequiredMixin):
    allowed_roles = ["ADMIN", "MANAGER"]


class InventoryStaffUpMixin(RoleRequiredMixin):
    allowed_roles = ["ADMIN", "MANAGER", "INVENTORY_STAFF"]


class CashierUpMixin(RoleRequiredMixin):
    """Anyone who can operate the POS: cashiers and above."""
    allowed_roles = ["ADMIN", "MANAGER", "CASHIER"]


class AuditableMixin:
    """Mixin for CreateView/UpdateView/DeleteView that writes an AuditLog
    entry automatically. Set `audit_action` on the view, e.g. "PRODUCT_ADDED".
    """
    audit_action = None

    def _write_audit(self, action, instance, old_value="", new_value=""):
        from audit.utils import log_action
        log_action(
            request=self.request,
            action=action or self.audit_action,
            target=instance,
            old_value=old_value,
            new_value=new_value,
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        self._write_audit(self.audit_action, self.object, new_value=str(self.object))
        return response

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        old_value = str(self.object)
        response = super().delete(request, *args, **kwargs)
        self._write_audit(self.audit_action, None, old_value=old_value)
        return response
