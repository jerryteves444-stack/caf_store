from django import forms
from accounts.forms import StyledFormMixin
from .models import Customer


class CustomerForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "address", "phone_number", "email", "credit_limit", "is_active"]


class PaymentForm(StyledFormMixin, forms.Form):
    amount = forms.DecimalField(min_value=0.01, decimal_places=2)
    payment_method = forms.ChoiceField(choices=[("CASH", "Cash")])
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))


class DebtSearchForm(StyledFormMixin, forms.Form):
    q = forms.CharField(required=False, label="Search customer")
    status = forms.ChoiceField(
        choices=[("", "All"), ("PAID", "Paid"), ("PARTIAL", "Partially Paid"), ("UNPAID", "Unpaid"), ("OVERDUE", "Overdue")],
        required=False,
    )
