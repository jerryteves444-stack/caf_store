from django.test import TestCase
from django.urls import reverse
from .models import User, Role


class UserModelTests(TestCase):
    def test_role_properties(self):
        admin = User.objects.create_user(username="a", password="pass12345", role=Role.ADMIN)
        cashier = User.objects.create_user(username="c", password="pass12345", role=Role.CASHIER)
        self.assertTrue(admin.is_admin)
        self.assertTrue(admin.can_operate_pos)
        self.assertFalse(cashier.is_admin)
        self.assertTrue(cashier.can_operate_pos)
        self.assertFalse(cashier.can_manage_inventory)


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass12345", role=Role.CASHIER)

    def test_login_success(self):
        response = self.client.post(reverse("accounts:login"), {"username": "tester", "password": "pass12345"})
        self.assertEqual(response.status_code, 302)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
