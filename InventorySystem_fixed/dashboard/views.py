import json
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.views.generic import TemplateView

from customers.models import Customer, CustomerDebt, PaymentStatus
from inventory.models import Product
from meat.models import MeatInventory
from sales.models import Sale, SaleItem
from suppliers.models import Supplier


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        month_start = today.replace(day=1)

        sales_qs = Sale.objects.filter(is_voided=False)
        today_sales = sales_qs.filter(created_at__date=today).aggregate(total=Sum("total_amount"))["total"] or 0
        monthly_sales = sales_qs.filter(created_at__date__gte=month_start).aggregate(total=Sum("total_amount"))["total"] or 0
        total_revenue = sales_qs.aggregate(total=Sum("total_amount"))["total"] or 0

        products = Product.objects.all()
        meats = MeatInventory.objects.all()

        ctx.update({
            "today_sales": today_sales,
            "monthly_sales": monthly_sales,
            "total_revenue": total_revenue,
            "total_products": products.count(),
            "total_customers": Customer.objects.count(),
            "total_suppliers": Supplier.objects.count(),
            "total_meat_inventory_kg": sum(m.remaining_stock_kg for m in meats),
            "total_livestock_batches": meats.count(),
            "low_stock_products": [p for p in products if p.is_low_stock],
            "out_of_stock_products": [p for p in products if p.is_out_of_stock],
            "customers_with_debt": CustomerDebt.objects.exclude(payment_status=PaymentStatus.PAID).select_related("customer")[:10],
            "recent_transactions": sales_qs.select_related("customer", "cashier").order_by("-created_at")[:10],
        })

        # ---- chart data --------------------------------------------------
        last_14_days = today - timedelta(days=13)
        daily = (
            sales_qs.filter(created_at__date__gte=last_14_days)
            .annotate(day=TruncDate("created_at"))
            .values("day").annotate(total=Sum("total_amount")).order_by("day")
        )
        ctx["daily_sales_labels"] = json.dumps([d["day"].strftime("%b %d") for d in daily])
        ctx["daily_sales_values"] = json.dumps([float(d["total"]) for d in daily])

        last_12_months = today.replace(day=1) - timedelta(days=365)
        monthly = (
            sales_qs.filter(created_at__date__gte=last_12_months)
            .annotate(month=TruncMonth("created_at"))
            .values("month").annotate(total=Sum("total_amount")).order_by("month")
        )
        ctx["monthly_sales_labels"] = json.dumps([m["month"].strftime("%b %Y") for m in monthly])
        ctx["monthly_sales_values"] = json.dumps([float(m["total"]) for m in monthly])

        best_sellers = (
            SaleItem.objects.filter(sale__is_voided=False, item_type="PRODUCT")
            .values("product__name").annotate(units=Sum("quantity")).order_by("-units")[:5]
        )
        ctx["best_seller_labels"] = json.dumps([b["product__name"] for b in best_sellers])
        ctx["best_seller_values"] = json.dumps([float(b["units"]) for b in best_sellers])

        inventory_levels = products.order_by("-quantity")[:8]
        ctx["inventory_labels"] = json.dumps([p.name for p in inventory_levels])
        ctx["inventory_values"] = json.dumps([p.quantity for p in inventory_levels])

        category_counts = products.values("category__name").annotate(count=Count("id"))
        ctx["category_labels"] = json.dumps([c["category__name"] for c in category_counts])
        ctx["category_values"] = json.dumps([c["count"] for c in category_counts])

        return ctx
