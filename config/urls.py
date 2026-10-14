from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("academic/", include("apps.academics.urls")),
    path("practicals/", include("apps.practicals.urls")),
    path("reports/", include("apps.reporting.urls")),
    path("", include("apps.core.urls")),
]
