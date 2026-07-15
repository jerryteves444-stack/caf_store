from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from core.mixins import InventoryStaffUpMixin, AuditableMixin
from audit.models import AuditLog
from .forms import SupplierForm
from .models import Supplier


class SupplierListView(InventoryStaffUpMixin, ListView):
    model = Supplier
    template_name = "suppliers/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(company_name__icontains=q) | Q(contact_person__icontains=q))
        return qs


class SupplierDetailView(InventoryStaffUpMixin, DetailView):
    model = Supplier
    template_name = "suppliers/supplier_detail.html"
    context_object_name = "supplier"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["products"] = self.object.products.all()
        ctx["purchase_orders"] = self.object.purchase_orders.order_by("-created_at")[:20]
        return ctx


class SupplierCreateView(InventoryStaffUpMixin, AuditableMixin, SuccessMessageMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "suppliers/supplier_form.html"
    success_url = reverse_lazy("suppliers:supplier_list")
    success_message = "Supplier added."
    audit_action = AuditLog.Action.OTHER


class SupplierUpdateView(InventoryStaffUpMixin, AuditableMixin, SuccessMessageMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "suppliers/supplier_form.html"
    success_url = reverse_lazy("suppliers:supplier_list")
    success_message = "Supplier updated."
    audit_action = AuditLog.Action.OTHER


class SupplierDeleteView(InventoryStaffUpMixin, AuditableMixin, DeleteView):
    model = Supplier
    template_name = "suppliers/supplier_confirm_delete.html"
    success_url = reverse_lazy("suppliers:supplier_list")
    audit_action = AuditLog.Action.OTHER
