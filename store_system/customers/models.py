from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Customer(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("customers:customer_detail", kwargs={"pk": self.pk})

    @property
    def total_outstanding_balance(self):
        return self.debts.exclude(payment_status=PaymentStatus.PAID).aggregate(
            total=models.Sum("remaining_balance")
        )["total"] or Decimal("0.00")

    @property
    def available_credit(self):
        return self.credit_limit - self.total_outstanding_balance


class PaymentStatus(models.TextChoices):
    PAID = "PAID", "Paid"
    PARTIALLY_PAID = "PARTIAL", "Partially Paid"
    UNPAID = "UNPAID", "Unpaid"
    OVERDUE = "OVERDUE", "Overdue"


class CustomerDebt(models.Model):
    """One row per credit sale. `sale` links back to the originating Sale
    so products purchased / cashier / date are all derivable, while the
    balance/due-date/status fields specific to credit tracking live here."""

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="debts")
    sale = models.OneToOneField("sales.Sale", on_delete=models.CASCADE, related_name="debt_record", null=True, blank=True)

    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["payment_status", "due_date"])]

    def __str__(self):
        return f"{self.customer.name} - {self.remaining_balance} due {self.due_date}"

    def refresh_status(self):
        if self.remaining_balance <= 0:
            self.payment_status = PaymentStatus.PAID
        elif self.amount_paid > 0:
            self.payment_status = PaymentStatus.PARTIALLY_PAID
        else:
            self.payment_status = PaymentStatus.UNPAID
        if self.payment_status != PaymentStatus.PAID and self.due_date < timezone.now().date():
            self.payment_status = PaymentStatus.OVERDUE
        self.save(update_fields=["payment_status"])


class CustomerPayment(models.Model):
    """Every partial/full payment against a CustomerDebt. Recording a
    payment here is the single source of truth that recalculates the
    parent debt's remaining_balance (see customers/services.py)."""

    debt = models.ForeignKey(CustomerDebt, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, default="CASH")
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_at"]

    def __str__(self):
        return f"Payment {self.amount} for {self.debt.customer.name}"
