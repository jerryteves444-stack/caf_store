from django import forms
from accounts.forms import StyledFormMixin
from .models import Product, ProductCategory, InventoryTransaction


class ProductForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "product_code", "name", "product_type", "category", "supplier", "unit",
            "cost_price", "selling_price", "wholesale_price", "promo_price", "discount_price",
            "quantity", "reorder_level", "expiration_date", "image", "is_active",
        ]
        widgets = {
            "expiration_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        cost = cleaned.get("cost_price")
        selling = cleaned.get("selling_price")
        if cost is not None and selling is not None and selling < cost:
            self.add_error("selling_price", "Selling price should not be lower than cost price.")
        return cleaned


class ProductCategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ["name", "description"]


class StockAdjustmentForm(StyledFormMixin, forms.Form):
    ACTION_CHOICES = [("IN", "Stock In"), ("OUT", "Stock Out"), ("SET", "Set exact quantity (adjustment)")]
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    quantity = forms.IntegerField(min_value=0)
    batch_number = forms.CharField(required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))


class ProductSearchForm(StyledFormMixin, forms.Form):
    q = forms.CharField(required=False, label="Search")
    category = forms.ModelChoiceField(queryset=ProductCategory.objects.all(), required=False)
    product_type = forms.ChoiceField(choices=[("", "All types")] + list(Product._meta.get_field("product_type").choices), required=False)
    stock_status = forms.ChoiceField(
        choices=[("", "All"), ("LOW", "Low Stock"), ("OUT", "Out of Stock"), ("EXPIRING", "Expiring Soon")],
        required=False,
    )
