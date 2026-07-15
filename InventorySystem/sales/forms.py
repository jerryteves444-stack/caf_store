from django import forms
from accounts.forms import StyledFormMixin
from .models import PaymentMethod


class CheckoutForm(StyledFormMixin, forms.Form):
    """The cart itself is built client-side (JS) and posted as JSON in
    `cart_data`; this form validates the transaction-level fields."""
    customer_id = forms.IntegerField(required=False)
    payment_method = forms.ChoiceField(choices=PaymentMethod.choices, initial=PaymentMethod.CASH)
    amount_tendered = forms.DecimalField(required=False, min_value=0, decimal_places=2)
    discount_amount = forms.DecimalField(required=False, min_value=0, decimal_places=2, initial=0)
    cart_data = forms.CharField(widget=forms.HiddenInput)
