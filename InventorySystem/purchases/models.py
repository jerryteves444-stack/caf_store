from django.conf import settings
from django.db import models


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ORDERED = "ORDERED", "Ordered"
    PARTIALLY_RECEIVED = "PARTIAL", "Partially Received"
    RECEIVED = "RECEIVED", "Received"
    CANCELLED = "CANCELLED", "Cancelled"


class PurchaseOrder(models.Model):
    po_number = models.CharField(max_length=30, unique=True, db_index=True)
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=10, choices=PurchaseOrderStatus.choices, default=PurchaseOrderStatus.DRAFT)
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PO-{self.po_number} ({self.supplier.company_name})"

    @property
    def total_cost(self):
        return sum((item.quantity_ordered * item.unit_cost for item in self.items.all()), start=0)


class PurchaseItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="purchase_items", null=True, blank=True)
    meat = models.ForeignKey("meat.MeatInventory", on_delete=models.PROTECT, related_name="purchase_items", null=True, blank=True)
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        pass

    def __str__(self):
        target = self.product or self.meat
        return f"{target} x {self.quantity_ordered}"

    @property
    def line_total(self):
        return self.quantity_ordered * self.unit_cost

    @property
    def is_fully_received(self):
        return self.quantity_received >= self.quantity_ordered
