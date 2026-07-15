from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    LOW_STOCK = "LOW_STOCK", "Low Stock"
    OUT_OF_STOCK = "OUT_OF_STOCK", "Out of Stock"
    EXPIRING = "EXPIRING", "Expiring Product"
    PAYMENT_DUE = "PAYMENT_DUE", "Customer Payment Due"
    OVERDUE_ACCOUNT = "OVERDUE", "Overdue Customer Account"
    NEW_PURCHASE_ORDER = "NEW_PO", "New Purchase Order"
    PAYMENT_RECORDED = "PAYMENT_RECORDED", "Payment Recorded"


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.message}"
