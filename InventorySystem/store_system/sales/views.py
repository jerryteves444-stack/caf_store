import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView, DetailView

from core.mixins import CashierUpMixin, ManagerUpMixin
from customers.models import Customer
from inventory.models import Product
from meat.models import MeatInventory

from . import services
from .models import Sale, SaleItemType, PaymentMethod


class POSView(CashierUpMixin, View):
    """The point-of-sale screen. Product/meat catalogues are dumped as
    JSON for instant client-side search/barcode-scan filtering; the cart
    itself lives in JS state until checkout is submitted."""

    def get(self, request):
        products = Product.objects.filter(is_active=True, quantity__gt=0).values(
            "id", "product_code", "name", "selling_price", "promo_price", "discount_price", "quantity", "barcode_value"
        )
        meats = MeatInventory.objects.filter(is_active=True, remaining_stock_kg__gt=0).values(
            "id", "meat_code", "meat_type", "selling_price_per_kg", "remaining_stock_kg"
        )
        customers = Customer.objects.filter(is_active=True).values("id", "name", "credit_limit")
        context = {
            "products_json": json.dumps(list(products), default=str),
            "meats_json": json.dumps(list(meats), default=str),
            "customers_json": json.dumps(list(customers), default=str),
            "payment_methods": PaymentMethod.choices,
        }
        return render(request, "sales/pos.html", context)


class CheckoutAPIView(CashierUpMixin, View):
    """AJAX endpoint the POS page posts to when the cashier hits "Complete Sale"."""

    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8"))
            cart_lines = [
                services.CartLine(
                    item_type=line["item_type"],
                    item_id=int(line["item_id"]),
                    quantity=Decimal(str(line["quantity"])),
                    line_discount=Decimal(str(line.get("line_discount", 0))),
                )
                for line in payload.get("cart", [])
            ]
            customer = None
            if payload.get("customer_id"):
                customer = get_object_or_404(Customer, pk=payload["customer_id"])

            sale = services.checkout(
                cart_lines=cart_lines,
                cashier=request.user,
                customer=customer,
                payment_method=payload.get("payment_method", PaymentMethod.CASH),
                amount_tendered=Decimal(str(payload["amount_tendered"])) if payload.get("amount_tendered") else None,
                discount_amount=Decimal(str(payload.get("discount_amount", 0))),
            )
            return JsonResponse({"success": True, "redirect_url": f"/sales/{sale.pk}/receipt/"})
        except (ValidationError, KeyError, InvalidOperation, ValueError) as exc:
            return JsonResponse({"success": False, "error": str(exc)}, status=400)


class SaleHistoryListView(CashierUpMixin, ListView):
    model = Sale
    template_name = "sales/sale_history.html"
    context_object_name = "sales"
    paginate_by = 25

    def get_queryset(self):
        qs = Sale.objects.select_related("customer", "cashier").order_by("-created_at")
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if q:
            qs = qs.filter(Q(invoice_number__icontains=q) | Q(customer__name__icontains=q))
        if status:
            qs = qs.filter(payment_status=status)
        return qs


class SaleReceiptView(CashierUpMixin, DetailView):
    model = Sale
    template_name = "sales/receipt.html"
    context_object_name = "sale"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.all()
        return ctx


class VoidSaleView(ManagerUpMixin, View):
    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        reason = request.POST.get("reason", "")
        services.void_sale(sale, user=request.user, reason=reason)
        messages.success(request, f"Sale {sale.invoice_number} voided; stock restored.")
        return redirect("sales:sale_history")
