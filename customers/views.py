from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from core.mixins import CashierUpMixin, InventoryStaffUpMixin, AuditableMixin
from audit.models import AuditLog
from . import services
from .forms import CustomerForm, PaymentForm, DebtSearchForm
from .models import Customer, CustomerDebt


class CustomerListView(CashierUpMixin, ListView):
    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(phone_number__icontains=q))
        return qs


class CustomerDetailView(CashierUpMixin, DetailView):
    model = Customer
    template_name = "customers/customer_detail.html"
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["debts"] = self.object.debts.order_by("-created_at")
        ctx["sales"] = self.object.sales.order_by("-created_at")[:20] if hasattr(self.object, "sales") else []
        return ctx


class CustomerCreateView(CashierUpMixin, AuditableMixin, SuccessMessageMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"
    success_url = reverse_lazy("customers:customer_list")
    success_message = "Customer added."
    audit_action = AuditLog.Action.OTHER


class CustomerUpdateView(CashierUpMixin, AuditableMixin, SuccessMessageMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"
    success_url = reverse_lazy("customers:customer_list")
    success_message = "Customer updated."
    audit_action = AuditLog.Action.OTHER


# ---- Debt tracking ----------------------------------------------------

class DebtListView(CashierUpMixin, ListView):
    model = CustomerDebt
    template_name = "customers/debt_list.html"
    context_object_name = "debts"
    paginate_by = 25

    def get_queryset(self):
        qs = CustomerDebt.objects.select_related("customer").order_by("-created_at")
        form = DebtSearchForm(self.request.GET or None)
        if form.is_valid():
            q = form.cleaned_data.get("q")
            status = form.cleaned_data.get("status")
            if q:
                qs = qs.filter(customer__name__icontains=q)
            if status:
                qs = qs.filter(payment_status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_form"] = DebtSearchForm(self.request.GET or None)
        return ctx


class DebtDetailView(CashierUpMixin, DetailView):
    model = CustomerDebt
    template_name = "customers/debt_detail.html"
    context_object_name = "debt"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["payments"] = self.object.payments.order_by("-paid_at")
        ctx["payment_form"] = PaymentForm()
        return ctx


class RecordPaymentView(CashierUpMixin, View):
    def post(self, request, pk):
        debt = get_object_or_404(CustomerDebt, pk=pk)
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                services.record_payment(
                    debt, form.cleaned_data["amount"], user=request.user,
                    payment_method=form.cleaned_data["payment_method"], notes=form.cleaned_data["notes"],
                )
                messages.success(request, "Payment recorded and balance updated.")
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, "Invalid payment data.")
        return redirect("customers:debt_detail", pk=pk)


class CustomerStatementView(CashierUpMixin, DetailView):
    """Printable statement (browser print-to-PDF); a dedicated minimal
    template with no sidebar so it prints cleanly."""
    model = Customer
    template_name = "customers/customer_statement.html"
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["debts"] = self.object.debts.order_by("-created_at")
        return ctx
