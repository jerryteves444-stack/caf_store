from datetime import datetime

from django.views import View
from django.shortcuts import render

from core.mixins import ManagerUpMixin
from . import services
from .exporters import export_csv, export_excel, export_pdf


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


class SalesReportView(ManagerUpMixin, View):
    def get(self, request):
        period = request.GET.get("period", "daily")
        start = _parse_date(request.GET.get("start"))
        end = _parse_date(request.GET.get("end"))
        data = list(services.sales_report(period, start, end))
        best_sellers = list(services.best_selling_products(start=start, end=end))

        export = request.GET.get("export")
        if export:
            headers = ["Period", "Total Sales", "Transaction Count"]
            rows = [[d["period"], d["total_sales"], d["transaction_count"]] for d in data]
            return self._export(export, "sales_report", "Sales Report", headers, rows)

        return render(request, "reports/sales_report.html", {
            "data": data, "best_sellers": best_sellers, "period": period, "start": start, "end": end,
        })

    def _export(self, fmt, filename, title, headers, rows):
        if fmt == "csv":
            return export_csv(filename, headers, rows)
        if fmt == "excel":
            return export_excel(filename, headers, rows, sheet_title=title)
        if fmt == "pdf":
            return export_pdf(filename, title, headers, rows)
        return export_csv(filename, headers, rows)


class InventoryReportView(ManagerUpMixin, View):
    def get(self, request):
        report_type = request.GET.get("type", "current")
        if report_type == "low_stock":
            products = services.low_stock_report()
        elif report_type == "out_of_stock":
            products = services.out_of_stock_report()
        elif report_type == "expiring":
            products = services.expiring_products_report()
        else:
            products = list(services.current_inventory_report())

        export = request.GET.get("export")
        if export:
            headers = ["Code", "Name", "Category", "Quantity", "Reorder Level", "Cost Price", "Selling Price", "Expiration"]
            rows = [
                [p.product_code, p.name, p.category.name, p.quantity, p.reorder_level, p.cost_price, p.selling_price, p.expiration_date or ""]
                for p in products
            ]
            return SalesReportView()._export(export, f"inventory_{report_type}", "inventory Report", headers, rows)

        return render(request, "reports/inventory_report.html", {"products": products, "report_type": report_type})


class DebtReportView(ManagerUpMixin, View):
    def get(self, request):
        status = request.GET.get("status") or None
        debts = list(services.debt_report(status))

        export = request.GET.get("export")
        if export:
            headers = ["Customer", "Total", "Paid", "Balance", "Due Date", "Status"]
            rows = [
                [d.customer.name, d.total_amount, d.amount_paid, d.remaining_balance, d.due_date, d.get_payment_status_display()]
                for d in debts
            ]
            return SalesReportView()._export(export, "debt_report", "Debt Report", headers, rows)

        return render(request, "reports/debt_report.html", {"debts": debts, "status": status})


class FinancialReportView(ManagerUpMixin, View):
    def get(self, request):
        start = _parse_date(request.GET.get("start"))
        end = _parse_date(request.GET.get("end"))
        summary = services.financial_report(start, end)

        export = request.GET.get("export")
        if export:
            headers = ["Revenue", "Expenses (COGS)", "Profit", "Sale Count"]
            rows = [[summary["revenue"], summary["expenses_cogs"], summary["profit"], summary["sale_count"]]]
            return SalesReportView()._export(export, "financial_report", "Financial Report", headers, rows)

        return render(request, "reports/financial_report.html", {"summary": summary, "start": start, "end": end})
