from django import forms
from accounts.forms import StyledFormMixin
from .models import MeatInventory


class MeatInventoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = MeatInventory
        fields = [
            "meat_code", "meat_type", "supplier", "weight_kg", "remaining_stock_kg",
            "cost_per_kg", "selling_price_per_kg", "batch_number", "expiration_date", "is_active",
        ]
        widgets = {"expiration_date": forms.DateInput(attrs={"type": "date"})}


class MeatStockForm(StyledFormMixin, forms.Form):
    ACTION_CHOICES = [("RECEIVE", "Receive Stock"), ("WASTE", "Record Wastage")]
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    weight_kg = forms.DecimalField(min_value=0, decimal_places=2)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
