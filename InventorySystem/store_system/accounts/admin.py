from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "is_active_employee", "is_staff", "date_joined")
    list_filter = ("role", "is_active_employee", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Store profile", {"fields": ("role", "phone_number", "avatar", "must_change_password", "is_active_employee")}),
    )
