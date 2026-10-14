from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.PlatformLoginView.as_view(), name="login"),
    path("logout/", views.platform_logout, name="logout"),
    path("password/change/", views.PlatformPasswordChangeView.as_view(), name="password_change"),
    path("approvals/", views.pending_approvals, name="pending_approvals"),
    path("approvals/<int:user_id>/approve/", views.approve_account, name="approve_account"),
    path("approvals/<int:user_id>/reject/", views.reject_account, name="reject_account"),
    path("manage/", views.user_management, name="user_management"),
    path("manage/<int:user_id>/<str:action>/access/", views.account_availability, name="account_availability"),
    path("manage/<int:user_id>/reset-password/", views.admin_password_reset, name="admin_password_reset"),
]
