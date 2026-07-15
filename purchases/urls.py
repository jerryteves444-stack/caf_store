from django.urls import path
from . import views

app_name = "purchases"

urlpatterns = [
    path("", views.PurchaseOrderListView.as_view(), name="po_list"),
    path("add/", views.PurchaseOrderCreateView.as_view(), name="po_add"),
    path("<int:pk>/", views.PurchaseOrderDetailView.as_view(), name="po_detail"),
    path("<int:pk>/receive/", views.ReceiveDeliveryView.as_view(), name="po_receive"),
]
