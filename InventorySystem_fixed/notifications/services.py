from django.utils import timezone

from .models import Notification, NotificationType


def _broadcast(notification_type, message, link="", roles=("ADMIN", "MANAGER", "INVENTORY_STAFF")):
    from accounts.models import User
    recipients = User.objects.filter(role__in=roles, is_active=True, is_active_employee=True)
    # Avoid re-spamming the same unread alert every time a signal fires.
    existing = set(
        Notification.objects.filter(
            notification_type=notification_type, message=message, is_read=False
        ).values_list("recipient_id", flat=True)
    )
    to_create = [
        Notification(recipient=u, notification_type=notification_type, message=message, link=link)
        for u in recipients if u.id not in existing
    ]
    if to_create:
        Notification.objects.bulk_create(to_create)


def notify_low_stock(product):
    _broadcast(
        NotificationType.LOW_STOCK,
        f"Low stock: {product.name} ({product.quantity} left, reorder level {product.reorder_level}).",
        link=f"/inventory/products/{product.pk}/",
    )


def notify_out_of_stock(product):
    _broadcast(
        NotificationType.OUT_OF_STOCK,
        f"Out of stock: {product.name}.",
        link=f"/inventory/products/{product.pk}/",
    )


def notify_low_stock_meat(meat):
    _broadcast(
        NotificationType.LOW_STOCK,
        f"Low meat stock: {meat.get_meat_type_display()} batch {meat.meat_code} ({meat.remaining_stock_kg}kg left).",
        link=f"/meat/{meat.pk}/",
    )


def notify_out_of_stock_meat(meat):
    _broadcast(
        NotificationType.OUT_OF_STOCK,
        f"Out of meat stock: {meat.get_meat_type_display()} batch {meat.meat_code}.",
        link=f"/meat/{meat.pk}/",
    )


def notify_expiring_product(product):
    _broadcast(
        NotificationType.EXPIRING,
        f"Expiring soon: {product.name} on {product.expiration_date}.",
        link=f"/inventory/products/{product.pk}/",
    )


def notify_payment_due(debt):
    _broadcast(
        NotificationType.PAYMENT_DUE,
        f"Payment due soon: {debt.customer.name} owes {debt.remaining_balance} (due {debt.due_date}).",
        link=f"/customers/debts/{debt.pk}/",
        roles=("ADMIN", "MANAGER", "CASHIER"),
    )


def notify_overdue_account(debt):
    _broadcast(
        NotificationType.OVERDUE_ACCOUNT,
        f"Overdue account: {debt.customer.name} owes {debt.remaining_balance} (due {debt.due_date}).",
        link=f"/customers/debts/{debt.pk}/",
        roles=("ADMIN", "MANAGER", "CASHIER"),
    )


def notify_payment_recorded(debt):
    _broadcast(
        NotificationType.PAYMENT_RECORDED,
        f"Payment recorded for {debt.customer.name}; remaining balance {debt.remaining_balance}.",
        link=f"/customers/debts/{debt.pk}/",
        roles=("ADMIN", "MANAGER"),
    )


def notify_new_purchase_order(po):
    _broadcast(
        NotificationType.NEW_PURCHASE_ORDER,
        f"New purchase order {po.po_number} for {po.supplier.company_name}.",
        link=f"/purchases/{po.pk}/",
    )
