from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction

from .models import CustomerDebt, CustomerPayment


@db_transaction.atomic
def record_payment(debt: CustomerDebt, amount, user=None, payment_method="CASH", notes=""):
    debt = CustomerDebt.objects.select_for_update().get(pk=debt.pk)
    if amount <= 0:
        raise ValidationError("Payment amount must be greater than zero.")
    if amount > debt.remaining_balance:
        raise ValidationError(
            f"Payment ({amount}) exceeds remaining balance ({debt.remaining_balance})."
        )

    CustomerPayment.objects.create(
        debt=debt, amount=amount, payment_method=payment_method, notes=notes, received_by=user
    )
    debt.amount_paid += amount
    debt.remaining_balance -= amount
    debt.save(update_fields=["amount_paid", "remaining_balance", "updated_at"])
    debt.refresh_status()

    from notifications.services import notify_payment_recorded
    notify_payment_recorded(debt)
    return debt
