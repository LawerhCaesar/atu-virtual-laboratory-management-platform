from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class PlatformUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "approval_status", "is_active")
    list_filter = ("role", "approval_status", "is_active")
    search_fields = ("email", "full_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identity", {"fields": ("full_name", "role", "approval_status")}),
        ("Review", {"fields": ("reviewed_by", "reviewed_at", "must_change_password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "password1", "password2"),
            },
        ),
    )

