from django import forms
from accounts.forms import StyledFormMixin
from .models import Supplier


class SupplierForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["company_name", "contact_person", "address", "phone", "email", "is_active"]
