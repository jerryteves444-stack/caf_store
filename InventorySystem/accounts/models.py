from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Administrator"
    MANAGER = "MANAGER", "Manager"
    CASHIER = "CASHIER", "Cashier"
    INVENTORY_STAFF = "INVENTORY_STAFF", "inventory Staff"


class User(AbstractUser):
    """Custom user model. Password hashing, session handling, and the
    login/logout machinery are all inherited from Django's battle-tested
    auth system (PBKDF2 hashing by default)."""

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CASHIER)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    must_change_password = models.BooleanField(
        default=False, help_text="Force password change on next login (e.g. after admin reset)."
    )
    is_active_employee = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_user"
        ordering = ["username"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == Role.ADMIN or self.is_superuser

    @property
    def is_manager(self):
        return self.role in (Role.ADMIN, Role.MANAGER) or self.is_superuser

    @property
    def can_manage_inventory(self):
        return self.role in (Role.ADMIN, Role.MANAGER, Role.INVENTORY_STAFF) or self.is_superuser

    @property
    def can_operate_pos(self):
        return self.role in (Role.ADMIN, Role.MANAGER, Role.CASHIER) or self.is_superuser
