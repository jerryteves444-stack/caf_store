from django.contrib import admin
from .models import MeatInventory, MeatTransaction


@admin.register(MeatInventory)
class MeatInventoryAdmin(admin.ModelAdmin):
    list_display = ("meat_code", "meat_type", "remaining_stock_kg", "selling_price_per_kg", "expiration_date", "is_active")
    list_filter = ("meat_type", "is_active")
    search_fields = ("meat_code", "batch_number")


@admin.register(MeatTransaction)
class MeatTransactionAdmin(admin.ModelAdmin):
    list_display = ("meat", "transaction_type", "weight_kg", "performed_by", "created_at")
    list_filter = ("transaction_type",)
