from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class MeatType(models.TextChoices):
    PORK = "PORK", "Pork"
    BEEF = "BEEF", "Beef"
    CHICKEN = "CHICKEN", "Chicken"
    GOAT = "GOAT", "Goat Meat"
    OTHER = "OTHER", "Other"


class MeatInventory(models.Model):
    """Fresh meat is priced and sold by weight (kg) rather than by piece,
    so it gets its own model instead of reusing inventory.Product."""

    meat_code = models.CharField(max_length=30, unique=True, db_index=True)
    meat_type = models.CharField(max_length=10, choices=MeatType.choices)
    supplier = models.ForeignKey(
        "suppliers.Supplier", on_delete=models.SET_NULL, null=True, blank=True, related_name="meat_supplies"
    )

    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="Weight received in this batch (kg).")
    remaining_stock_kg = models.DecimalField(max_digits=10, decimal_places=2)

    cost_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)

    batch_number = models.CharField(max_length=50, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Meat inventory"
        ordering = ["meat_type", "-created_at"]
        indexes = [models.Index(fields=["meat_type"]), models.Index(fields=["expiration_date"])]

    def __str__(self):
        return f"{self.meat_code} - {self.get_meat_type_display()} ({self.remaining_stock_kg}kg)"

    def get_absolute_url(self):
        return reverse("meat:meat_detail", kwargs={"pk": self.pk})

    @property
    def is_low_stock(self):
        return 0 < self.remaining_stock_kg <= 5  # 5kg threshold; tweak as needed

    @property
    def is_out_of_stock(self):
        return self.remaining_stock_kg <= 0

    @property
    def is_expiring_soon(self):
        if not self.expiration_date:
            return False
        from django.conf import settings as dj_settings
        days = getattr(dj_settings, "EXPIRY_WARNING_DAYS", 7)
        return 0 <= (self.expiration_date - timezone.now().date()).days <= days


class MeatTransactionType(models.TextChoices):
    RECEIVE = "RECEIVE", "Stock Received"
    SALE = "SALE", "Sale Deduction"
    ADJUSTMENT = "ADJUST", "Adjustment"
    WASTAGE = "WASTE", "Wastage / Spoilage"


class MeatTransaction(models.Model):
    meat = models.ForeignKey(MeatInventory, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=MeatTransactionType.choices)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="Signed: positive=in, negative=out")
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.meat} ({self.weight_kg}kg)"
