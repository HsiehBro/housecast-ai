from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_active")
    search_fields = ("username", "email", "phone")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = UserAdmin.fieldsets + (
        ("扩展信息", {
            "fields": ("phone", "avatar", "created_at", "updated_at"),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("扩展信息", {
            "fields": ("phone",),
        }),
    )
