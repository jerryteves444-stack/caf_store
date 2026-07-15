from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/add/", views.ProductCreateView.as_view(), name="product_add"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("products/<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
    path("products/<int:pk>/adjust-stock/", views.StockAdjustmentView.as_view(), name="product_adjust_stock"),
    path("low-stock/", views.LowStockListView.as_view(), name="low_stock"),
    path("expiring/", views.ExpiringProductsListView.as_view(), name="expiring"),
]
