from django.urls import path

from . import views


app_name = "academics"

urlpatterns = [
    path("setup/<int:user_id>/", views.academic_setup, name="setup"),
    path("courses/", views.course_list, name="course_list"),
    path("courses/new/", views.course_create, name="course_create"),
    path("offerings/", views.offering_list, name="offering_list"),
    path("offerings/new/", views.offering_create, name="offering_create"),
    path("offerings/<int:offering_id>/access/", views.offering_access, name="offering_access"),
]
