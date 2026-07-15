from django.urls import path
from . import views

app_name = "meat"

urlpatterns = [
    path("", views.MeatListView.as_view(), name="meat_list"),
    path("add/", views.MeatCreateView.as_view(), name="meat_add"),
    path("<int:pk>/", views.MeatDetailView.as_view(), name="meat_detail"),
    path("<int:pk>/edit/", views.MeatUpdateView.as_view(), name="meat_edit"),
    path("<int:pk>/delete/", views.MeatDeleteView.as_view(), name="meat_delete"),
    path("<int:pk>/stock/", views.MeatStockUpdateView.as_view(), name="meat_stock_update"),
]
