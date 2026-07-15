import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Cash"
    CREDIT = "CREDIT", "Store Credit (Customer Debt)"


class SalePaymentStatus(models.TextChoices):
    PAID = "PAID", "Paid"
    PARTIALLY_PAID = "PARTIAL", "Partially Paid"
    UNPAID = "UNPAID", "Unpaid"


class Sale(models.Model):
    """A completed (or in-progress) POS transaction. Invoice numbers are
    generated sequentially per day for readability; `uuid_ref` is a
    collision-proof internal reference used in barcodes/receipts."""

    invoice_number = models.CharField(max_length=30, unique=True, db_index=True)
    uuid_ref = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales"
    )
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sales_made")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    payment_status = models.CharField(max_length=10, choices=SalePaymentStatus.choices, default=SalePaymentStatus.PAID)
    amount_tendered = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    change_due = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    is_voided = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at"]), models.Index(fields=["payment_status"])]

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    def get_absolute_url(self):
        return reverse("sales:sale_receipt", kwargs={"pk": self.pk})


class SaleItemType(models.TextChoices):
    PRODUCT = "PRODUCT", "Product (canned/dry goods)"
    MEAT = "MEAT", "Fresh Meat"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=10, choices=SaleItemType.choices)

    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, null=True, blank=True, related_name="sale_items")
    meat = models.ForeignKey("meat.MeatInventory", on_delete=models.PROTECT, null=True, blank=True, related_name="sale_items")

    description = models.CharField(max_length=200, help_text="Snapshot of product/meat name at time of sale")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Units for products, kg for meat")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        pass

    def __str__(self):
        return f"{self.description} x {self.quantity}"

    @property
    def line_total(self):
        return (self.quantity * self.unit_price) - self.line_discount
