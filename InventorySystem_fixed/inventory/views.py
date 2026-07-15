from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import get_object_or_404, redirect, render

from core.mixins import InventoryStaffUpMixin, AuditableMixin
from audit.models import AuditLog
from . import services
from .forms import ProductForm, ProductSearchForm, StockAdjustmentForm
from .models import Product, InventoryTransaction


class ProductListView(InventoryStaffUpMixin, ListView):
    """Searchable, filterable, paginated product catalogue (CRUD: Read)."""
    model = Product
    template_name = "inventory/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related("category", "supplier")
        form = ProductSearchForm(self.request.GET or None)
        if form.is_valid():
            q = form.cleaned_data.get("q")
            category = form.cleaned_data.get("category")
            product_type = form.cleaned_data.get("product_type")
            stock_status = form.cleaned_data.get("stock_status")
            if q:
                qs = qs.filter(Q(name__icontains=q) | Q(product_code__icontains=q))
            if category:
                qs = qs.filter(category=category)
            if product_type:
                qs = qs.filter(product_type=product_type)
            if stock_status == "LOW":
                qs = [p for p in qs if p.is_low_stock]
            elif stock_status == "OUT":
                qs = [p for p in qs if p.is_out_of_stock]
            elif stock_status == "EXPIRING":
                qs = [p for p in qs if p.is_expiring_soon]
        sort = self.request.GET.get("sort", "name")
        if isinstance(qs, list):
            return qs
        allowed_sorts = {"name", "-name", "quantity", "-quantity", "selling_price", "-selling_price", "product_code"}
        if sort in allowed_sorts:
            qs = qs.order_by(sort)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_form"] = ProductSearchForm(self.request.GET or None)
        return ctx


class ProductDetailView(InventoryStaffUpMixin, DetailView):
    model = Product
    template_name = "inventory/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = self.object.transactions.select_related("performed_by")[:25]
        ctx["price_history"] = self.object.price_history.select_related("changed_by")[:25] if hasattr(self.object, "price_history") else []
        ctx["adjustment_form"] = StockAdjustmentForm()
        return ctx


class ProductCreateView(InventoryStaffUpMixin, AuditableMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy("inventory:product_list")
    success_message = "Product added successfully."
    audit_action = AuditLog.Action.PRODUCT_ADDED

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProductUpdateView(InventoryStaffUpMixin, AuditableMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy("inventory:product_list")
    success_message = "Product updated successfully."
    audit_action = AuditLog.Action.PRODUCT_EDITED

    def form_valid(self, form):
        old_price = Product.objects.get(pk=self.object.pk).selling_price
        response = super().form_valid(form)
        new_price = form.instance.selling_price
        if old_price != new_price:
            from pricing.models import PriceHistory
            PriceHistory.objects.create(
                product=self.object, old_price=old_price, new_price=new_price,
                changed_by=self.request.user, reason="Manual edit via product form",
            )
        return response


class ProductDeleteView(InventoryStaffUpMixin, AuditableMixin, View):
    """Deletion requires an explicit confirmation POST (see template)."""
    audit_action = AuditLog.Action.PRODUCT_DELETED

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return render(request, "inventory/product_confirm_delete.html", {"product": product})

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        name = str(product)
        product.delete()
        self._write_audit(self.audit_action, None, old_value=name)
        messages.success(request, "Product deleted permanently.")
        return redirect("inventory:product_list")


class StockAdjustmentView(InventoryStaffUpMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            qty = form.cleaned_data["quantity"]
            notes = form.cleaned_data["notes"]
            batch = form.cleaned_data["batch_number"]
            try:
                if action == "IN":
                    services.stock_in(product, qty, user=request.user, notes=notes, batch_number=batch)
                elif action == "OUT":
                    services.stock_out(product, qty, user=request.user, notes=notes)
                else:
                    services.manual_adjustment(product, qty, user=request.user, notes=notes)
                messages.success(request, "Inventory updated.")
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, "Invalid stock adjustment data.")
        return redirect("inventory:product_detail", pk=pk)


class LowStockListView(InventoryStaffUpMixin, ListView):
    template_name = "inventory/low_stock.html"
    context_object_name = "products"

    def get_queryset(self):
        return [p for p in Product.objects.all() if p.is_low_stock or p.is_out_of_stock]


class ExpiringProductsListView(InventoryStaffUpMixin, ListView):
    template_name = "inventory/expiring.html"
    context_object_name = "products"

    def get_queryset(self):
        return [p for p in Product.objects.exclude(expiration_date=None) if p.is_expiring_soon]
