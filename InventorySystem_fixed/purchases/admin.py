from django.contrib import admin
from .models import PurchaseOrder, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("po_number", "supplier", "status", "expected_date", "created_at")
    list_filter = ("status",)
    inlines = [PurchaseItemInline]
