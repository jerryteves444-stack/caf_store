from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.utils import timezone

from sales.models import Sale, SaleItem
from inventory.models import Product
from meat.models import MeatInventory
from customers.models import CustomerDebt, CustomerPayment, PaymentStatus


PERIOD_TRUNC = {"daily": TruncDate, "weekly": TruncWeek, "monthly": TruncMonth, "annual": TruncYear}


def sales_report(period="daily", start=None, end=None):
    qs = Sale.objects.filter(is_voided=False)
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)
    trunc = PERIOD_TRUNC.get(period, TruncDate)
    return (
        qs.annotate(period=trunc("created_at"))
        .values("period")
        .annotate(total_sales=Sum("total_amount"), transaction_count=Count("id"))
        .order_by("period")
    )


def best_selling_products(limit=10, start=None, end=None):
    qs = SaleItem.objects.filter(sale__is_voided=False, item_type="PRODUCT")
    if start:
        qs = qs.filter(sale__created_at__date__gte=start)
    if end:
        qs = qs.filter(sale__created_at__date__lte=end)
    return (
        qs.values("product__name")
        .annotate(units_sold=Sum("quantity"), revenue=Sum(F("quantity") * F("unit_price")))
        .order_by("-units_sold")[:limit]
    )


def current_inventory_report():
    return Product.objects.select_related("category").order_by("category__name", "name")


def stock_movement_report(start=None, end=None):
    from inventory.models import InventoryTransaction
    qs = InventoryTransaction.objects.select_related("product", "performed_by")
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)
    return qs.order_by("-created_at")


def low_stock_report():
    return [p for p in Product.objects.all() if p.is_low_stock]


def out_of_stock_report():
    return [p for p in Product.objects.all() if p.is_out_of_stock]


def expiring_products_report():
    return [p for p in Product.objects.exclude(expiration_date=None) if p.is_expiring_soon]


def debt_report(status=None):
    qs = CustomerDebt.objects.select_related("customer")
    if status:
        qs = qs.filter(payment_status=status)
    return qs.order_by("-created_at")


def payment_history_report(start=None, end=None):
    qs = CustomerPayment.objects.select_related("debt__customer", "received_by")
    if start:
        qs = qs.filter(paid_at__date__gte=start)
    if end:
        qs = qs.filter(paid_at__date__lte=end)
    return qs.order_by("-paid_at")


def financial_report(start=None, end=None):
    """Revenue, approximate COGS (cost_price snapshot via current product
    cost -- for a fully historical COGS you'd snapshot cost at sale time),
    and profit."""
    sales_qs = Sale.objects.filter(is_voided=False)
    if start:
        sales_qs = sales_qs.filter(created_at__date__gte=start)
    if end:
        sales_qs = sales_qs.filter(created_at__date__lte=end)

    revenue = sales_qs.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

    cogs = Decimal("0.00")
    items = SaleItem.objects.filter(sale__in=sales_qs, item_type="PRODUCT").select_related("product")
    for item in items:
        if item.product:
            cogs += item.quantity * item.product.cost_price
    meat_items = SaleItem.objects.filter(sale__in=sales_qs, item_type="MEAT").select_related("meat")
    for item in meat_items:
        if item.meat:
            cogs += item.quantity * item.meat.cost_per_kg

    profit = revenue - cogs
    return {"revenue": revenue, "expenses_cogs": cogs, "profit": profit, "sale_count": sales_qs.count()}
