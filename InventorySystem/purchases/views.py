from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, View

from core.mixins import InventoryStaffUpMixin
from . import services
from .forms import PurchaseOrderForm, PurchaseItemFormSet
from .models import PurchaseOrder


class PurchaseOrderListView(InventoryStaffUpMixin, ListView):
    model = PurchaseOrder
    template_name = "purchases/po_list.html"
    context_object_name = "purchase_orders"
    paginate_by = 20

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related("supplier").order_by("-created_at")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class PurchaseOrderDetailView(InventoryStaffUpMixin, DetailView):
    model = PurchaseOrder
    template_name = "purchases/po_detail.html"
    context_object_name = "po"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.select_related("product", "meat")
        return ctx


class PurchaseOrderCreateView(InventoryStaffUpMixin, View):
    def get(self, request):
        form = PurchaseOrderForm()
        formset = PurchaseItemFormSet()
        return render(request, "purchases/po_form.html", {"form": form, "formset": formset})

    def post(self, request):
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            formset.instance = po
            formset.save()
            messages.success(request, f"Purchase order {po.po_number} created.")
            return redirect("purchases:po_detail", pk=po.pk)
        return render(request, "purchases/po_form.html", {"form": form, "formset": formset})


class ReceiveDeliveryView(InventoryStaffUpMixin, View):
    def get(self, request, pk):
        po = get_object_or_404(PurchaseOrder, pk=pk)
        return render(request, "purchases/receive_delivery.html", {"po": po, "items": po.items.all()})

    def post(self, request, pk):
        po = get_object_or_404(PurchaseOrder, pk=pk)
        received = {}
        for item in po.items.all():
            raw = request.POST.get(f"qty_{item.id}")
            if raw:
                try:
                    received[item.id] = Decimal(raw)
                except InvalidOperation:
                    continue
        services.receive_delivery(po, received, user=request.user)
        messages.success(request, "Delivery received. inventory updated automatically.")
        return redirect("purchases:po_detail", pk=pk)
