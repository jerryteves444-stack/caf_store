from django.urls import path
from . import views

app_name = "pricing"

urlpatterns = [
    path("history/", views.PriceHistoryListView.as_view(), name="price_history"),
    path("products/<int:pk>/override/", views.PriceOverrideView.as_view(), name="price_override"),
    path("markup-calculator/", views.MarkupCalculatorView.as_view(), name="markup_calculator"),
    path("promotions/", views.PromoScheduleListView.as_view(), name="promo_list"),
    path("promotions/add/", views.PromoScheduleCreateView.as_view(), name="promo_add"),
]
