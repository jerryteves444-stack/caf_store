from django import forms
from accounts.forms import StyledFormMixin
from .models import PromoSchedule


class PriceOverrideForm(StyledFormMixin, forms.Form):
    new_price = forms.DecimalField(min_value=0, decimal_places=2)
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}))


class MarkupCalculatorForm(StyledFormMixin, forms.Form):
    cost_price = forms.DecimalField(min_value=0, decimal_places=2)
    markup_percent = forms.DecimalField(min_value=0, decimal_places=2, initial=30)


class PromoScheduleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PromoSchedule
        fields = ["product", "promo_price", "start_date", "end_date", "is_active"]
        widgets = {
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
