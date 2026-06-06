from django.contrib import admin
from .models import House


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = (
        "name", "district", "area", "rooms", "halls",
        "floor", "total_floors", "year", "orientation",
        "decoration", "price", "price_per_sqm", "status",
        "created_at",
    )
    list_filter = ("district", "status", "orientation", "decoration", "property_type")
    search_fields = ("name", "address", "district")
    readonly_fields = ("price_per_sqm", "created_at", "updated_at")
    list_per_page = 20
    ordering = ("-created_at",)

    fieldsets = (
        ("基本信息", {
            "fields": ("name", "address", "district", "property_type", "status"),
        }),
        ("房屋属性", {
            "fields": (
                "area", "rooms", "halls", "bathrooms",
                "floor", "total_floors", "year",
                "orientation", "decoration",
            ),
        }),
        ("价格信息", {
            "fields": ("price", "price_per_sqm"),
        }),
        ("位置信息", {
            "fields": ("lat", "lng"),
        }),
        ("时间信息", {
            "fields": ("created_at", "updated_at"),
        }),
    )
