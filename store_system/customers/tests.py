from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase

from accounts.models import User, Role
from .models import Customer, CustomerDebt, PaymentStatus
from . import services


class PaymentServiceTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Debtor", credit_limit=Decimal("2000.00"))
        self.debt = CustomerDebt.objects.create(
            customer=self.customer, total_amount=Decimal("500.00"), remaining_balance=Decimal("500.00"),
            due_date=date.today() + timedelta(days=30),
        )
        self.user = User.objects.create_user(username="cashier", password="pass12345", role=Role.CASHIER)

    def test_partial_payment_updates_status(self):
        services.record_payment(self.debt, Decimal("200.00"), user=self.user)
        self.debt.refresh_from_db()
        self.assertEqual(self.debt.remaining_balance, Decimal("300.00"))
        self.assertEqual(self.debt.payment_status, PaymentStatus.PARTIALLY_PAID)

    def test_full_payment_marks_paid(self):
        services.record_payment(self.debt, Decimal("500.00"), user=self.user)
        self.debt.refresh_from_db()
        self.assertEqual(self.debt.payment_status, PaymentStatus.PAID)
