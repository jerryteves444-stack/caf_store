from django.conf import settings
from django.db import models
from django.utils import timezone


class PriceHistory(models.Model):
    """Immutable record of every price change for a Product. Kept generic
    (product FK is nullable + meat FK nullable) so both catalog products
    and fresh-meat batches share one history/report table."""

    product = models.ForeignKey(
        "inventory.Product", on_delete=models.CASCADE, related_name="price_history", null=True, blank=True
    )
    meat = models.ForeignKey(
        "meat.MeatInventory", on_delete=models.CASCADE, related_name="price_history", null=True, blank=True
    )
    old_price = models.DecimalField(max_digits=12, decimal_places=2)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Price history"
        ordering = ["-changed_at"]

    def __str__(self):
        target = self.product or self.meat
        return f"{target}: {self.old_price} -> {self.new_price}"


class PromoSchedule(models.Model):
    """Scheduled promotional pricing window. A management command
    (apply_scheduled_promos) activates/deactivates promo_price on Product
    when `start_date`/`end_date` are crossed -- run it via cron/Celery beat."""

    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE, related_name="promo_schedules")
    promo_price = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.product} promo {self.promo_price} ({self.start_date:%Y-%m-%d} - {self.end_date:%Y-%m-%d})"

    @property
    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
