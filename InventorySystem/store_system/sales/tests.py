from decimal import Decimal
from django.test import TestCase

from accounts.models import User, Role
from inventory.models import Product, ProductCategory, ProductType
from customers.models import Customer
from . import services
from .models import PaymentMethod, SaleItemType


class CheckoutServiceTests(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(name="Canned Goods")
        self.product = Product.objects.create(
            product_code="POS-001", name="Test Corned Beef", product_type=ProductType.CANNED_GOODS,
            category=self.category, cost_price=Decimal("45.00"), selling_price=Decimal("62.00"), quantity=20,
        )
        self.cashier = User.objects.create_user(username="cashier", password="pass12345", role=Role.CASHIER)
        self.customer = Customer.objects.create(name="Test Customer", credit_limit=Decimal("1000.00"))

    def test_cash_sale_deducts_inventory(self):
        cart = [services.CartLine(item_type=SaleItemType.PRODUCT, item_id=self.product.id, quantity=Decimal("3"))]
        sale = services.checkout(cart, cashier=self.cashier, payment_method=PaymentMethod.CASH)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 17)
        self.assertEqual(sale.payment_status, "PAID")

    def test_credit_sale_creates_debt(self):
        cart = [services.CartLine(item_type=SaleItemType.PRODUCT, item_id=self.product.id, quantity=Decimal("2"))]
        sale = services.checkout(cart, cashier=self.cashier, customer=self.customer, payment_method=PaymentMethod.CREDIT)
        self.assertTrue(hasattr(sale, "debt_record"))
        self.assertEqual(sale.debt_record.remaining_balance, sale.total_amount)
