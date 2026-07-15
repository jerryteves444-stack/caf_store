"""
Signal hooks for the inventory app. Heavy periodic checks (e.g. scanning
every product for expiry) are better run via the `check_expiring_products`
management command on a scheduler (cron / celery beat) rather than on every
save, so this module intentionally stays light.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product


@receiver(post_save, sender=Product)
def notify_if_expiring_soon(sender, instance, created, **kwargs):
    if instance.is_expiring_soon:
        from notifications.services import notify_expiring_product
        notify_expiring_product(instance)
