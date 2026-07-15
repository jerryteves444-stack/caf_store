"""
POS checkout logic. This is the one place that:
  1. creates the Sale + SaleItem rows,
  2. deducts inventory (products via inventory.services, meat via meat.services),
  3. computes tax/discount/total,
  4. creates a CustomerDebt row when payment_method == CREDIT.
Keeping this in one atomic service function avoids partial/inconsistent
sales if any step fails.
"""
from dataclasses import dataclass, field
from datetime import timedelta, date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.utils import timezone

from inventory import services as inventory_services
from inventory.models import Product
from meat import services as meat_services
from meat.models import MeatInventory

from .models import Sale, SaleItem, SaleItemType, PaymentMethod, SalePaymentStatus


@dataclass
class CartLine:
    item_type: str  # "PRODUCT" or "MEAT"
    item_id: int
    quantity: Decimal
    line_discount: Decimal = Decimal("0.00")


def _next_invoice_number():
    today = timezone.now().strftime("%Y%m%d")
    count_today = Sale.objects.filter(invoice_number__startswith=f"INV-{today}").count() + 1
    return f"INV-{today}-{count_today:04d}"


@db_transaction.atomic
def checkout(
    cart_lines,
    cashier,
    customer=None,
    payment_method=PaymentMethod.CASH,
    amount_tendered=None,
    discount_amount=Decimal("0.00"),
    tax_rate=None,
    credit_due_days=30,
):
    """cart_lines: list[CartLine]. Returns the created Sale."""
    if not cart_lines:
        raise ValidationError("Cannot complete a sale with an empty cart.")
    if payment_method == PaymentMethod.CREDIT and customer is None:
        raise ValidationError("A customer must be selected for credit (on-account) sales.")

    tax_rate = Decimal(str(tax_rate if tax_rate is not None else getattr(settings, "DEFAULT_TAX_RATE", 0.12)))

    sale = Sale.objects.create(
        invoice_number=_next_invoice_number(),
        customer=customer,
        cashier=cashier,
        payment_method=payment_method,
        discount_amount=discount_amount,
    )

    subtotal = Decimal("0.00")

    for line in cart_lines:
        if line.item_type == SaleItemType.PRODUCT:
            product = Product.objects.select_for_update().get(pk=line.item_id)
            unit_price = product.current_price
            SaleItem.objects.create(
                sale=sale, item_type=SaleItemType.PRODUCT, product=product,
                description=product.name, quantity=line.quantity, unit_price=unit_price,
                line_discount=line.line_discount,
            )
            inventory_services.deduct_for_sale(product, int(line.quantity), user=cashier, reference=sale.invoice_number)
            subtotal += (line.quantity * unit_price) - line.line_discount

        elif line.item_type == SaleItemType.MEAT:
            meat = MeatInventory.objects.select_for_update().get(pk=line.item_id)
            unit_price = meat.selling_price_per_kg
            SaleItem.objects.create(
                sale=sale, item_type=SaleItemType.MEAT, meat=meat,
                description=meat.get_meat_type_display(), quantity=line.quantity, unit_price=unit_price,
                line_discount=line.line_discount,
            )
            meat_services.deduct_for_sale(meat, line.quantity, user=cashier, reference=sale.invoice_number)
            subtotal += (line.quantity * unit_price) - line.line_discount
        else:
            raise ValidationError(f"Unknown cart line item_type: {line.item_type}")

    taxable_amount = max(subtotal - discount_amount, Decimal("0.00"))
    tax_amount = (taxable_amount * tax_rate).quantize(Decimal("0.01"))
    total_amount = taxable_amount + tax_amount

    sale.subtotal = subtotal
    sale.tax_amount = tax_amount
    sale.total_amount = total_amount

    if payment_method == PaymentMethod.CASH:
        tendered = amount_tendered if amount_tendered is not None else total_amount
        if tendered < total_amount:
            raise ValidationError("Amount tendered is less than the total due.")
        sale.amount_tendered = tendered
        sale.change_due = tendered - total_amount
        sale.payment_status = SalePaymentStatus.PAID
        sale.save()
    else:
        sale.payment_status = SalePaymentStatus.UNPAID
        sale.save()
        from customers.models import CustomerDebt
        CustomerDebt.objects.create(
            customer=customer,
            sale=sale,
            total_amount=total_amount,
            amount_paid=Decimal("0.00"),
            remaining_balance=total_amount,
            due_date=date.today() + timedelta(days=credit_due_days),
        )

    from audit.utils import log_action
    from audit.models import AuditLog
    log_action(request=None, action=AuditLog.Action.SALE_COMPLETED, user=cashier, target=sale, new_value=str(sale))

    return sale


@db_transaction.atomic
def void_sale(sale: Sale, user, reason=""):
    """Reverses inventory deductions and marks the sale voided. Does not
    delete the row -- financial records should never be hard-deleted."""
    if sale.is_voided:
        return sale
    for item in sale.items.select_related("product", "meat"):
        if item.product:
            inventory_services.stock_in(item.product, int(item.quantity), user=user, reference=f"VOID-{sale.invoice_number}", notes=reason)
        elif item.meat:
            meat_services.receive_stock(item.meat, item.quantity, user=user, reference=f"VOID-{sale.invoice_number}")
    sale.is_voided = True
    sale.save(update_fields=["is_voided"])
    return sale
