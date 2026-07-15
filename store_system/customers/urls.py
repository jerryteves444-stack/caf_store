from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
    path("", views.CustomerListView.as_view(), name="customer_list"),
    path("add/", views.CustomerCreateView.as_view(), name="customer_add"),
    path("<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer_edit"),
    path("<int:pk>/statement/", views.CustomerStatementView.as_view(), name="customer_statement"),

    path("debts/", views.DebtListView.as_view(), name="debt_list"),
    path("debts/<int:pk>/", views.DebtDetailView.as_view(), name="debt_detail"),
    path("debts/<int:pk>/pay/", views.RecordPaymentView.as_view(), name="debt_pay"),
]
