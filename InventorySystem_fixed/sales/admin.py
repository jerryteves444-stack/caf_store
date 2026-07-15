from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer", "cashier", "total_amount", "payment_method", "payment_status", "created_at")
    list_filter = ("payment_method", "payment_status", "is_voided")
    search_fields = ("invoice_number",)
    inlines = [SaleItemInline]
