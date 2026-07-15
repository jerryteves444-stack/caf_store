from django.db.models import Q
from django.views.generic import ListView

from core.mixins import ManagerUpMixin
from .models import AuditLog


class AuditLogListView(ManagerUpMixin, ListView):
    model = AuditLog
    template_name = "audit/audit_log_list.html"
    context_object_name = "logs"
    paginate_by = 40

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user").order_by("-created_at")
        q = self.request.GET.get("q")
        action = self.request.GET.get("action")
        if q:
            qs = qs.filter(Q(user__username__icontains=q) | Q(target_repr__icontains=q))
        if action:
            qs = qs.filter(action=action)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["actions"] = AuditLog.Action.choices
        return ctx
