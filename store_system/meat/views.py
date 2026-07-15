from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from core.mixins import InventoryStaffUpMixin, AuditableMixin
from audit.models import AuditLog
from . import services
from .forms import MeatInventoryForm, MeatStockForm
from .models import MeatInventory


class MeatListView(InventoryStaffUpMixin, ListView):
    model = MeatInventory
    template_name = "meat/meat_list.html"
    context_object_name = "meats"
    paginate_by = 20

    def get_queryset(self):
        qs = MeatInventory.objects.select_related("supplier")
        q = self.request.GET.get("q")
        meat_type = self.request.GET.get("meat_type")
        if q:
            qs = qs.filter(Q(meat_code__icontains=q) | Q(batch_number__icontains=q))
        if meat_type:
            qs = qs.filter(meat_type=meat_type)
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["meat_types"] = MeatInventory._meta.get_field("meat_type").choices
        ctx["total_stock_kg"] = sum(m.remaining_stock_kg for m in self.get_queryset())
        return ctx


class MeatDetailView(InventoryStaffUpMixin, DetailView):
    model = MeatInventory
    template_name = "meat/meat_detail.html"
    context_object_name = "meat"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = self.object.transactions.select_related("performed_by")[:25]
        ctx["stock_form"] = MeatStockForm()
        return ctx


class MeatCreateView(InventoryStaffUpMixin, AuditableMixin, SuccessMessageMixin, CreateView):
    model = MeatInventory
    form_class = MeatInventoryForm
    template_name = "meat/meat_form.html"
    success_url = reverse_lazy("meat:meat_list")
    success_message = "Meat batch added to inventory."
    audit_action = AuditLog.Action.PRODUCT_ADDED

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class MeatUpdateView(InventoryStaffUpMixin, AuditableMixin, SuccessMessageMixin, UpdateView):
    model = MeatInventory
    form_class = MeatInventoryForm
    template_name = "meat/meat_form.html"
    success_url = reverse_lazy("meat:meat_list")
    success_message = "Meat inventory updated."
    audit_action = AuditLog.Action.PRODUCT_EDITED


class MeatDeleteView(InventoryStaffUpMixin, AuditableMixin, View):
    audit_action = AuditLog.Action.PRODUCT_DELETED

    def get(self, request, pk):
        meat = get_object_or_404(MeatInventory, pk=pk)
        return render(request, "meat/meat_confirm_delete.html", {"meat": meat})

    def post(self, request, pk):
        meat = get_object_or_404(MeatInventory, pk=pk)
        name = str(meat)
        meat.delete()
        self._write_audit(self.audit_action, None, old_value=name)
        messages.success(request, "Meat batch deleted.")
        return redirect("meat:meat_list")


class MeatStockUpdateView(InventoryStaffUpMixin, View):
    def post(self, request, pk):
        meat = get_object_or_404(MeatInventory, pk=pk)
        form = MeatStockForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            weight = form.cleaned_data["weight_kg"]
            notes = form.cleaned_data["notes"]
            try:
                if action == "RECEIVE":
                    services.receive_stock(meat, weight, user=request.user)
                else:
                    services.record_wastage(meat, weight, user=request.user, notes=notes)
                messages.success(request, "Meat stock updated.")
            except Exception as exc:
                messages.error(request, str(exc))
        return redirect("meat:meat_detail", pk=pk)
