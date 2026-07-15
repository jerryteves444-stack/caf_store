from django.core.management.base import BaseCommand
from pricing.services import apply_active_promotions


class Command(BaseCommand):
    help = "Activates/deactivates PromoSchedule promo pricing based on start/end dates. Run via cron every few minutes."

    def handle(self, *args, **options):
        activated, deactivated = apply_active_promotions()
        self.stdout.write(self.style.SUCCESS(f"Promotions activated: {activated}, deactivated: {deactivated}"))
