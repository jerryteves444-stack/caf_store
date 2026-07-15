from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("sales/", views.SalesReportView.as_view(), name="sales_report"),
    path("inventory/", views.InventoryReportView.as_view(), name="inventory_report"),
    path("debts/", views.DebtReportView.as_view(), name="debt_report"),
    path("financial/", views.FinancialReportView.as_view(), name="financial_report"),
]
