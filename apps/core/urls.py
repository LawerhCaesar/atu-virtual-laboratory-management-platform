from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("virtual-lab/", views.laboratory, name="laboratory"),
    path("virtual-lab/systems/<slug:system_slug>/", views.laboratory_system, name="laboratory_system"),
    path("virtual-lab/engine-live-data/", views.engine_live_data, name="engine_live_data"),
    path("health/ready/", views.readiness, name="readiness"),
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("help/", views.help_page, name="help"),
    path("management/settings/", views.platform_settings, name="platform_settings"),
    path("management/notices/", views.notice_management, name="notice_management"),
    path("management/notices/new/", views.notice_create, name="notice_create"),
    path("management/notices/<int:notice_id>/", views.notice_detail, name="notice_detail"),
    path("management/notices/<int:notice_id>/send/", views.notice_send, name="notice_send"),
    path("management/notices/<int:notice_id>/cancel/", views.notice_cancel, name="notice_cancel"),
    path("management/support/", views.support_management, name="support_management"),
    path("management/support/<int:ticket_id>/", views.support_review, name="support_review"),
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/<int:notification_id>/open/", views.notification_open, name="notification_open"),
]
