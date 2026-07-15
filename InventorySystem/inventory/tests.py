from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from accounts.models import User, Role
from .models import Product, ProductCategory, ProductType
from . import services


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(name="Canned Goods")
        self.product = Product.objects.create(
            product_code="TEST-001", name="Test Sardines", product_type=ProductType.CANNED_GOODS,
            category=self.category, cost_price=Decimal("15.00"), selling_price=Decimal("22.00"),
            quantity=5, reorder_level=10,
        )

    def test_low_stock_flag(self):
        self.assertTrue(self.product.is_low_stock)

    def test_out_of_stock_flag(self):
        self.product.quantity = 0
        self.product.save()
        self.assertTrue(self.product.is_out_of_stock)

    def test_current_price_promo_override(self):
        self.product.promo_price = Decimal("18.00")
        self.product.save()
        self.assertEqual(self.product.current_price, Decimal("18.00"))


class InventoryServiceTests(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(name="Dry Goods")
        self.product = Product.objects.create(
            product_code="TEST-002", name="Test Rice", product_type=ProductType.DRY_GOODS,
            category=self.category, cost_price=Decimal("40.00"), selling_price=Decimal("55.00"), quantity=10,
        )
        self.user = User.objects.create_user(username="staff", password="pass12345", role=Role.INVENTORY_STAFF)

    def test_stock_in_increases_quantity(self):
        services.stock_in(self.product, 5, user=self.user)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 15)

    def test_stock_out_decreases_quantity(self):
        services.stock_out(self.product, 4, user=self.user)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 6)

    def test_stock_out_cannot_go_negative(self):
        with self.assertRaises(ValidationError):
            services.stock_out(self.product, 999, user=self.user)
