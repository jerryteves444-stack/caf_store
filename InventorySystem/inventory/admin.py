from .models import ProductCategory, Product, InventoryTransaction
from django.contrib import admin
from .models import ProductCategory, Product, InventoryTransaction


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_code", "name", "product_type", "category", "quantity", "selling_price", "is_active")
    list_filter = ("product_type", "category", "is_active")
    search_fields = ("product_code", "name")


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("product", "transaction_type", "quantity", "performed_by", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("product__name", "reference")
