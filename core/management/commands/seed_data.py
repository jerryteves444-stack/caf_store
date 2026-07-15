"""
Seeds the database with sample data for demoing/development:
  - Users for each role (admin/manager/cashier/inventory staff)
  - Product categories, canned/dry goods, fresh meat
  - Suppliers, customers
  - A handful of sample sales (cash + credit) so dashboard charts have data

Usage: python manage.py seed_data
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, Role
from inventory.models import ProductCategory, Product, ProductType
from meat.models import MeatInventory, MeatType
from suppliers.models import Supplier
from customers.models import Customer
from sales import services as sales_services
from sales.models import PaymentMethod, SaleItemType


class Command(BaseCommand):
    help = "Populates the database with demo data."

    def handle(self, *args, **options):
        self.stdout.write("Seeding users...")
        users = self._seed_users()

        self.stdout.write("Seeding suppliers...")
        suppliers = self._seed_suppliers()

        self.stdout.write("Seeding categories & products...")
        products = self._seed_products(suppliers, users["inventory"])

        self.stdout.write("Seeding fresh meat...")
        meats = self._seed_meat(suppliers, users["inventory"])

        self.stdout.write("Seeding customers...")
        customers = self._seed_customers()

        self.stdout.write("Seeding sample sales...")
        self._seed_sales(products, meats, customers, users["cashier"])

        self.stdout.write(self.style.SUCCESS("Done! Sample login: admin / admin12345"))

    def _seed_users(self):
        admin, _ = User.objects.get_or_create(username="admin", defaults={
            "role": Role.ADMIN, "is_staff": True, "is_superuser": True, "email": "admin@example.com"
        })
        admin.set_password("admin12345")
        admin.save()

        manager, _ = User.objects.get_or_create(username="manager1", defaults={"role": Role.MANAGER, "email": "manager1@example.com"})
        manager.set_password("manager12345")
        manager.save()

        cashier, _ = User.objects.get_or_create(username="cashier1", defaults={"role": Role.CASHIER, "email": "cashier1@example.com"})
        cashier.set_password("cashier12345")
        cashier.save()

        inventory, _ = User.objects.get_or_create(username="inventory1", defaults={"role": Role.INVENTORY_STAFF, "email": "inventory1@example.com"})
        inventory.set_password("inventory12345")
        inventory.save()

        return {"admin": admin, "manager": manager, "cashier": cashier, "inventory": inventory}

    def _seed_suppliers(self):
        names = ["Golden Harvest Trading", "Metro Meat Packers", "Sunrise Grocery Distributors"]
        suppliers = []
        for n in names:
            s, _ = Supplier.objects.get_or_create(company_name=n, defaults={
                "contact_person": "Contact Person", "phone": "0917-000-0000", "email": f"{n.split()[0].lower()}@example.com"
            })
            suppliers.append(s)
        return suppliers

    def _seed_products(self, suppliers, staff_user):
        canned_cat, _ = ProductCategory.objects.get_or_create(name="Canned Goods")
        dry_cat, _ = ProductCategory.objects.get_or_create(name="Dry Goods")

        canned_items = [("Sardines in Tomato Sauce", 15, 22), ("Tuna Flakes in Oil", 25, 35), ("Corned Beef", 45, 62), ("Meat Loaf", 40, 55)]
        dry_items = [("Rice (Sack, 25kg)", 900, 1150), ("Sugar (kg)", 55, 68), ("All-Purpose Flour (kg)", 40, 52), ("Coffee (Sachet Pack)", 60, 78), ("Instant Noodles (Pack)", 8, 13)]

        products = []
        for i, (name, cost, price) in enumerate(canned_items, start=1):
            p, _ = Product.objects.get_or_create(product_code=f"CAN-{i:03d}", defaults={
                "name": name, "product_type": ProductType.CANNED_GOODS, "category": canned_cat,
                "supplier": random.choice(suppliers), "unit": "can",
                "cost_price": Decimal(cost), "selling_price": Decimal(price),
                "quantity": random.randint(20, 150), "reorder_level": 15,
                "expiration_date": date.today() + timedelta(days=random.randint(30, 365)),
                "created_by": staff_user,
            })
            products.append(p)

        for i, (name, cost, price) in enumerate(dry_items, start=1):
            p, _ = Product.objects.get_or_create(product_code=f"DRY-{i:03d}", defaults={
                "name": name, "product_type": ProductType.DRY_GOODS, "category": dry_cat,
                "supplier": random.choice(suppliers), "unit": "pc",
                "cost_price": Decimal(cost), "selling_price": Decimal(price),
                "quantity": random.randint(10, 100), "reorder_level": 10,
                "created_by": staff_user,
            })
            products.append(p)

        return products

    def _seed_meat(self, suppliers, staff_user):
        items = [(MeatType.PORK, 180, 240), (MeatType.BEEF, 280, 360), (MeatType.CHICKEN, 120, 165), (MeatType.GOAT, 260, 340)]
        meats = []
        for i, (mtype, cost, price) in enumerate(items, start=1):
            m, _ = MeatInventory.objects.get_or_create(meat_code=f"MEAT-{i:03d}", defaults={
                "meat_type": mtype, "supplier": random.choice(suppliers),
                "weight_kg": Decimal("50.00"), "remaining_stock_kg": Decimal(str(random.randint(5, 50))),
                "cost_per_kg": Decimal(cost), "selling_price_per_kg": Decimal(price),
                "expiration_date": date.today() + timedelta(days=random.randint(2, 10)),
                "created_by": staff_user,
            })
            meats.append(m)
        return meats

    def _seed_customers(self):
        names = ["Maria Santos", "Juan Dela Cruz", "Ana Reyes", "Pedro Ramos"]
        customers = []
        for n in names:
            c, _ = Customer.objects.get_or_create(name=n, defaults={
                "phone_number": "0917-111-2222", "credit_limit": Decimal("5000.00"),
            })
            customers.append(c)
        return customers

    def _seed_sales(self, products, meats, customers, cashier):
        for _ in range(15):
            cart = [
                sales_services.CartLine(item_type=SaleItemType.PRODUCT, item_id=random.choice(products).id, quantity=Decimal(random.randint(1, 3))),
            ]
            try:
                sales_services.checkout(cart, cashier=cashier, payment_method=PaymentMethod.CASH)
            except Exception:
                continue

        # a couple of credit sales
        for _ in range(3):
            cart = [
                sales_services.CartLine(item_type=SaleItemType.PRODUCT, item_id=random.choice(products).id, quantity=Decimal(2)),
            ]
            try:
                sales_services.checkout(cart, cashier=cashier, customer=random.choice(customers), payment_method=PaymentMethod.CREDIT)
            except Exception:
                continue
