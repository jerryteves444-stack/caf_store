# The dashboard app has no models of its own; it aggregates data from
# inventory, sales, customers, suppliers, and meat for display.
import io
import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.files.base import ContentFile
from django.utils import timezone


class ProductCategory(models.Model):
    """Top-level grouping, e.g. Canned Goods / Dry Goods / Beverages.
    Fresh Meat is modelled separately in the `meat` app because its
    fields (weight, per-kilo pricing) differ substantially."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductType(models.TextChoices):
    CANNED_GOODS = "CANNED", "Canned Goods"
    DRY_GOODS = "DRY", "Dry Goods"


class Product(models.Model):
    """Covers Canned Goods and Dry Goods. The two categories share almost
    every field; `product_type` toggles which optional fields apply
    (e.g. expiration_date is central to canned goods, reorder_level /
    unit / supplier matter more for dry goods, but both are kept on the
    same model so sales/reporting can query products uniformly)."""

    product_code = models.CharField(max_length=30, unique=True, db_index=True)
    name = models.CharField(max_length=150, db_index=True)
    product_type = models.CharField(max_length=10, choices=ProductType.choices)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name="products")
    supplier = models.ForeignKey(
        "suppliers.Supplier", on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )

    unit = models.CharField(max_length=20, default="pc", help_text="e.g. pc, sack, kg, box")

    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    promo_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    expiration_date = models.DateField(null=True, blank=True)

    barcode_value = models.CharField(max_length=64, unique=True, blank=True)
    barcode_image = models.ImageField(upload_to="barcodes/", blank=True, null=True)
    qr_code_image = models.ImageField(upload_to="qrcodes/", blank=True, null=True)

    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="products_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["product_type"]),
            models.Index(fields=["quantity"]),
            models.Index(fields=["expiration_date"]),
        ]

    def __str__(self):
        return f"{self.product_code} - {self.name}"

    def get_absolute_url(self):
        return reverse("inventory:product_detail", kwargs={"pk": self.pk})

    # ---- stock helpers ----------------------------------------------------
    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level and self.quantity > 0

    @property
    def is_out_of_stock(self):
        return self.quantity <= 0

    @property
    def is_expiring_soon(self):
        if not self.expiration_date:
            return False
        from django.conf import settings as dj_settings
        days = getattr(dj_settings, "EXPIRY_WARNING_DAYS", 7)
        return 0 <= (self.expiration_date - timezone.now().date()).days <= days

    @property
    def current_price(self):
        """Effective selling price honoring an active promo/discount."""
        return self.promo_price or self.discount_price or self.selling_price

    @property
    def margin(self):
        return (self.current_price or 0) - (self.cost_price or 0)

    # ---- barcode / QR generation -------------------------------------------
    def save(self, *args, **kwargs):
        if not self.barcode_value:
            self.barcode_value = self.product_code or uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)
        self._generate_barcode_and_qr()

    def _generate_barcode_and_qr(self):
        """Generates barcode/QR images once (or if missing). Uses python-barcode
        and qrcode; failures are swallowed so a missing optional dependency
        never blocks core CRUD operations."""
        try:
            if not self.barcode_image:
                import barcode
                from barcode.writer import ImageWriter
                code = barcode.get("code128", self.barcode_value, writer=ImageWriter())
                buffer = io.BytesIO()
                code.write(buffer)
                Product.objects.filter(pk=self.pk).update(
                    barcode_image=ContentFile(buffer.getvalue(), name=f"{self.barcode_value}.png")
                )
        except Exception:
            pass

        try:
            if not self.qr_code_image:
                import qrcode
                qr_data = f"PRODUCT:{self.product_code}:{self.name}"
                img = qrcode.make(qr_data)
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                Product.objects.filter(pk=self.pk).update(
                    qr_code_image=ContentFile(buffer.getvalue(), name=f"{self.barcode_value}_qr.png")
                )
        except Exception:
            pass


class TransactionType(models.TextChoices):
    STOCK_IN = "IN", "Stock In"
    STOCK_OUT = "OUT", "Stock Out"
    ADJUSTMENT = "ADJUST", "inventory Adjustment"
    SALE = "SALE", "Sale Deduction"
    PURCHASE_RECEIPT = "PURCHASE", "Purchase Receipt"


class InventoryTransaction(models.Model):
    """Immutable ledger of every stock movement. Product.quantity is a
    denormalised running total kept in sync by services in
    inventory/services.py; this table is the audit trail / batch tracker."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    quantity = models.IntegerField(help_text="Positive for stock in, negative for stock out (stored signed).")
    batch_number = models.CharField(max_length=50, blank=True)
    reference = models.CharField(max_length=100, blank=True, help_text="e.g. Sale #, PO #")
    notes = models.TextField(blank=True)

    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["transaction_type", "created_at"])]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity})"