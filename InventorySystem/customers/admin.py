from django.contrib import admin
from .models import Customer, CustomerDebt, CustomerPayment


class CustomerPaymentInline(admin.TabularInline):
    model = CustomerPayment
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "credit_limit", "is_active")
    search_fields = ("name", "phone_number")


@admin.register(CustomerDebt)
class CustomerDebtAdmin(admin.ModelAdmin):
    list_display = ("customer", "total_amount", "remaining_balance", "payment_status", "due_date")
    list_filter = ("payment_status",)
    inlines = [CustomerPaymentInline]
