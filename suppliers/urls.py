from django.urls import path
from . import views

app_name = "suppliers"

urlpatterns = [
    path("", views.SupplierListView.as_view(), name="supplier_list"),
    path("add/", views.SupplierCreateView.as_view(), name="supplier_add"),
    path("<int:pk>/", views.SupplierDetailView.as_view(), name="supplier_detail"),
    path("<int:pk>/edit/", views.SupplierUpdateView.as_view(), name="supplier_edit"),
    path("<int:pk>/delete/", views.SupplierDeleteView.as_view(), name="supplier_delete"),
]
