from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path("pos/", views.POSView.as_view(), name="pos"),
    path("pos/checkout/", views.CheckoutAPIView.as_view(), name="checkout_api"),
    path("", views.SaleHistoryListView.as_view(), name="sale_history"),
    path("<int:pk>/receipt/", views.SaleReceiptView.as_view(), name="sale_receipt"),
    path("<int:pk>/void/", views.VoidSaleView.as_view(), name="sale_void"),
]
