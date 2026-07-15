from django import forms
from django.forms import inlineformset_factory
from accounts.forms import StyledFormMixin
from .models import PurchaseOrder, PurchaseItem


class PurchaseOrderForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ["po_number", "supplier", "status", "expected_date", "notes"]
        widgets = {"expected_date": forms.DateInput(attrs={"type": "date"})}


class PurchaseItemForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ["product", "meat", "quantity_ordered", "unit_cost"]


PurchaseItemFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseItem, form=PurchaseItemForm, extra=1, can_delete=True
)


class ReceiveDeliveryForm(StyledFormMixin, forms.Form):
    """Rendered per line-item on the "receive delivery" screen."""
    item_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity_received_now = forms.DecimalField(min_value=0, decimal_places=2, required=False)
