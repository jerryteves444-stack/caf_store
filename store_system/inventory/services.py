"""
Central place for stock-mutating logic so Product.quantity is never
updated ad-hoc from views. Every function creates an InventoryTransaction
row (the audit ledger) and atomically updates Product.quantity.
"""
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError

from .models import Product, InventoryTransaction, TransactionType


@db_transaction.atomic
def adjust_stock(product: Product, delta: int, transaction_type: str, user=None, reference="", notes="", batch_number=""):
    """delta: positive to increase stock, negative to decrease.
    Raises ValidationError if a decrease would drop quantity below zero."""
    product = Product.objects.select_for_update().get(pk=product.pk)

    if delta < 0 and product.quantity + delta < 0:
        raise ValidationError(
            f"Insufficient stock for {product.name}: have {product.quantity}, need {abs(delta)}."
        )

    product.quantity = product.quantity + delta
    product.save(update_fields=["quantity", "updated_at"])

    InventoryTransaction.objects.create(
        product=product,
        transaction_type=transaction_type,
        quantity=delta,
        reference=reference,
        notes=notes,
        batch_number=batch_number,
        performed_by=user,
    )

    _maybe_notify_stock_level(product)
    return product


def stock_in(product, quantity, user=None, reference="", notes="", batch_number=""):
    return adjust_stock(product, abs(quantity), TransactionType.STOCK_IN, user, reference, notes, batch_number)


def stock_out(product, quantity, user=None, reference="", notes=""):
    return adjust_stock(product, -abs(quantity), TransactionType.STOCK_OUT, user, reference, notes)


def manual_adjustment(product, new_quantity, user=None, notes=""):
    delta = new_quantity - product.quantity
    return adjust_stock(product, delta, TransactionType.ADJUSTMENT, user, notes=notes)


def deduct_for_sale(product, quantity, user=None, reference=""):
    return adjust_stock(product, -abs(quantity), TransactionType.SALE, user, reference=reference)


def receive_purchase(product, quantity, user=None, reference=""):
    return adjust_stock(product, abs(quantity), TransactionType.PURCHASE_RECEIPT, user, reference=reference)


def _maybe_notify_stock_level(product: Product):
    from notifications.services import notify_low_stock, notify_out_of_stock
    if product.is_out_of_stock:
        notify_out_of_stock(product)
    elif product.is_low_stock:
        notify_low_stock(product)
