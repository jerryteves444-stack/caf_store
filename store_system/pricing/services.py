"""
Dynamic pricing engine.

- automatic markup calculation from cost price + a target margin %
- manual price override (logged to PriceHistory)
- scheduled promotional pricing (see management command apply_scheduled_promos)
"""
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone

from .models import PriceHistory, PromoSchedule


def calculate_markup_price(cost_price: Decimal, markup_percent: Decimal) -> Decimal:
    """Given a cost price and a target markup % (e.g. 30 for 30%), returns
    the suggested selling price, rounded to 2 decimals."""
    markup_percent = Decimal(markup_percent)
    price = Decimal(cost_price) * (Decimal("1") + markup_percent / Decimal("100"))
    return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def override_price(product, new_price: Decimal, user, reason: str = "Manual override"):
    """Manually sets a product's selling price and records the change."""
    old_price = product.selling_price
    if old_price == new_price:
        return product
    product.selling_price = new_price
    product.save(update_fields=["selling_price", "updated_at"])
    PriceHistory.objects.create(product=product, old_price=old_price, new_price=new_price, changed_by=user, reason=reason)
    return product


def apply_active_promotions():
    """Activates promo_price for products whose PromoSchedule window has
    started, and clears it for windows that have ended. Intended to run
    periodically (cron/Celery beat) via the apply_scheduled_promos command."""
    now = timezone.now()
    activated, deactivated = 0, 0

    starting = PromoSchedule.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)
    for promo in starting.select_related("product"):
        product = promo.product
        if product.promo_price != promo.promo_price:
            product.promo_price = promo.promo_price
            product.save(update_fields=["promo_price", "updated_at"])
            activated += 1

    ending = PromoSchedule.objects.filter(is_active=True, end_date__lt=now)
    for promo in ending.select_related("product"):
        product = promo.product
        if product.promo_price is not None:
            product.promo_price = None
            product.save(update_fields=["promo_price", "updated_at"])
        promo.is_active = False
        promo.save(update_fields=["is_active"])
        deactivated += 1

    return activated, deactivated
