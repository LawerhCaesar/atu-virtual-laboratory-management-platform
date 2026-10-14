from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "recipient", "category", "title", "read_at")
    list_filter = ("category", "created_at")
    search_fields = ("recipient__email", "recipient__full_name", "title", "message")
    readonly_fields = ("recipient", "category", "title", "message", "link", "read_at", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
