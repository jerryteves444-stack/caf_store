from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        LOGIN_FAILED = "LOGIN_FAILED", "Failed Login"
        PRODUCT_ADDED = "PRODUCT_ADDED", "Product Added"
        PRODUCT_EDITED = "PRODUCT_EDITED", "Product Edited"
        PRODUCT_DELETED = "PRODUCT_DELETED", "Product Deleted"
        INVENTORY_UPDATED = "INVENTORY_UPDATED", "inventory Updated"
        SALE_COMPLETED = "SALE_COMPLETED", "Sale Completed"
        CUSTOMER_PAYMENT = "CUSTOMER_PAYMENT", "Customer Payment"
        PRICE_CHANGED = "PRICE_CHANGED", "Price Changed"
        USER_MANAGEMENT = "USER_MANAGEMENT", "User Management"
        OTHER = "OTHER", "Other"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    action = models.CharField(max_length=30, choices=Action.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    target_repr = models.CharField(max_length=255, blank=True, help_text="String representation of the affected object")
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["action", "created_at"]), models.Index(fields=["user"])]

    def __str__(self):
        who = self.user.username if self.user else "system/anonymous"
        return f"{self.get_action_display()} by {who} at {self.created_at:%Y-%m-%d %H:%M}"
