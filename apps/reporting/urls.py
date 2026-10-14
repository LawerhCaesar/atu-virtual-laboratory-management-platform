from django.urls import path

from . import views


app_name = "reporting"

urlpatterns = [
    path("", views.report_dashboard, name="dashboard"),
    path("exports/users.csv", views.users_csv, name="users_csv"),
    path("exports/submissions.csv", views.submissions_csv, name="submissions_csv"),
    path("exports/summary.pdf", views.summary_pdf, name="summary_pdf"),
    path("audit/", views.audit_report, name="audit"),
    path("audit/export.csv", views.audit_csv, name="audit_csv"),
]

