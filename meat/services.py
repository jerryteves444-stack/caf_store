from decimal import Decimal
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError

from .models import MeatInventory, MeatTransaction, MeatTransactionType


@db_transaction.atomic
def adjust_weight(meat: MeatInventory, delta_kg: Decimal, transaction_type: str, user=None, reference="", notes=""):
    meat = MeatInventory.objects.select_for_update().get(pk=meat.pk)
    if delta_kg < 0 and meat.remaining_stock_kg + delta_kg < 0:
        raise ValidationError(
            f"Insufficient meat stock for {meat}: have {meat.remaining_stock_kg}kg, need {abs(delta_kg)}kg."
        )
    meat.remaining_stock_kg = meat.remaining_stock_kg + delta_kg
    meat.save(update_fields=["remaining_stock_kg", "updated_at"])
    MeatTransaction.objects.create(
        meat=meat, transaction_type=transaction_type, weight_kg=delta_kg,
        reference=reference, notes=notes, performed_by=user,
    )
    if meat.is_out_of_stock:
        from notifications.services import notify_out_of_stock_meat
        notify_out_of_stock_meat(meat)
    elif meat.is_low_stock:
        from notifications.services import notify_low_stock_meat
        notify_low_stock_meat(meat)
    return meat


def receive_stock(meat, weight_kg, user=None, reference=""):
    return adjust_weight(meat, abs(weight_kg), MeatTransactionType.RECEIVE, user, reference)


def deduct_for_sale(meat, weight_kg, user=None, reference=""):
    return adjust_weight(meat, -abs(weight_kg), MeatTransactionType.SALE, user, reference)


def record_wastage(meat, weight_kg, user=None, notes=""):
    return adjust_weight(meat, -abs(weight_kg), MeatTransactionType.WASTAGE, user, notes=notes)
