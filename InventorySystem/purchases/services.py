from django.db import transaction as db_transaction

from .models import PurchaseOrder, PurchaseOrderStatus


@db_transaction.atomic
def receive_delivery(purchase_order: PurchaseOrder, received_quantities: dict, user=None):
    """received_quantities: {purchase_item_id: Decimal quantity received now}.
    Automatically updates Product/MeatInventory stock (via their own
    services so InventoryTransaction / MeatTransaction ledgers stay
    consistent) and advances the PO status."""
    from inventory import services as inventory_services
    from meat import services as meat_services

    items = purchase_order.items.select_related("product", "meat")
    for item in items:
        qty_now = received_quantities.get(item.id)
        if not qty_now:
            continue
        item.quantity_received = min(item.quantity_ordered, item.quantity_received + qty_now)
        item.save(update_fields=["quantity_received"])

        reference = f"PO-{purchase_order.po_number}"
        if item.product:
            inventory_services.receive_purchase(item.product, int(qty_now), user=user, reference=reference)
        elif item.meat:
            meat_services.receive_stock(item.meat, qty_now, user=user, reference=reference)

    all_received = all(i.is_fully_received for i in purchase_order.items.all())
    any_received = any(i.quantity_received > 0 for i in purchase_order.items.all())
    if all_received:
        purchase_order.status = PurchaseOrderStatus.RECEIVED
    elif any_received:
        purchase_order.status = PurchaseOrderStatus.PARTIALLY_RECEIVED
    purchase_order.save(update_fields=["status", "updated_at"])
    return purchase_order
