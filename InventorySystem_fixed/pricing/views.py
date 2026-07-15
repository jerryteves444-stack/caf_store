from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, View

from core.mixins import ManagerUpMixin
from inventory.models import Product
from . import services
from .forms import PriceOverrideForm, MarkupCalculatorForm, PromoScheduleForm
from .models import PriceHistory, PromoSchedule


class PriceHistoryListView(ManagerUpMixin, ListView):
    model = PriceHistory
    template_name = "pricing/price_history_list.html"
    context_object_name = "history"
    paginate_by = 30

    def get_queryset(self):
        return PriceHistory.objects.select_related("product", "meat", "changed_by").order_by("-changed_at")


class PriceOverrideView(ManagerUpMixin, View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = PriceOverrideForm(initial={"new_price": product.selling_price})
        return render(request, "pricing/price_override_form.html", {"product": product, "form": form})

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = PriceOverrideForm(request.POST)
        if form.is_valid():
            services.override_price(product, form.cleaned_data["new_price"], request.user, form.cleaned_data["reason"])
            messages.success(request, "Price updated and logged to price history.")
            return redirect("inventory:product_detail", pk=pk)
        return render(request, "pricing/price_override_form.html", {"product": product, "form": form})


class MarkupCalculatorView(ManagerUpMixin, View):
    def get(self, request):
        return render(request, "pricing/markup_calculator.html", {"form": MarkupCalculatorForm()})

    def post(self, request):
        form = MarkupCalculatorForm(request.POST)
        result = None
        if form.is_valid():
            result = services.calculate_markup_price(form.cleaned_data["cost_price"], form.cleaned_data["markup_percent"])
        return render(request, "pricing/markup_calculator.html", {"form": form, "result": result})


class PromoScheduleListView(ManagerUpMixin, ListView):
    model = PromoSchedule
    template_name = "pricing/promo_list.html"
    context_object_name = "promos"


class PromoScheduleCreateView(ManagerUpMixin, CreateView):
    model = PromoSchedule
    form_class = PromoScheduleForm
    template_name = "pricing/promo_form.html"
    success_url = reverse_lazy("pricing:promo_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Promotional pricing scheduled.")
        return super().form_valid(form)
