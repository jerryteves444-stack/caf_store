from django.contrib import admin
from .models import PriceHistory, PromoSchedule


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("__str__", "changed_by", "changed_at")


@admin.register(PromoSchedule)
class PromoScheduleAdmin(admin.ModelAdmin):
    list_display = ("product", "promo_price", "start_date", "end_date", "is_active")
