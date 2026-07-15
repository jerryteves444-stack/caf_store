from django.core.management.base import BaseCommand
from django.utils import timezone

from customers.models import CustomerDebt, PaymentStatus
from inventory.models import Product
from notifications.services import notify_overdue_account, notify_expiring_product


class Command(BaseCommand):
    help = "Scans for overdue customer debts and expiring products, firing notifications. Run daily via cron."

    def handle(self, *args, **options):
        today = timezone.now().date()
        overdue_qs = CustomerDebt.objects.filter(due_date__lt=today).exclude(payment_status=PaymentStatus.PAID)
        for debt in overdue_qs:
            if debt.payment_status != PaymentStatus.OVERDUE:
                debt.payment_status = PaymentStatus.OVERDUE
                debt.save(update_fields=["payment_status"])
            notify_overdue_account(debt)

        expiring_count = 0
        for product in Product.objects.exclude(expiration_date=None):
            if product.is_expiring_soon:
                notify_expiring_product(product)
                expiring_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Overdue accounts flagged: {overdue_qs.count()}. Expiring products notified: {expiring_count}."
        ))
