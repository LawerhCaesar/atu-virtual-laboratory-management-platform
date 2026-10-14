from django.urls import path

from . import views


app_name = "practicals"

urlpatterns = [
    path("resources/", views.resource_list, name="resource_list"),
    path("resources/new/", views.resource_create, name="resource_create"),
    path("resources/<int:resource_id>/edit/", views.resource_edit, name="resource_edit"),
    path("resources/<int:resource_id>/revision/", views.resource_revision, name="resource_revision"),
    path("resources/<int:resource_id>/<str:action>/availability/", views.resource_availability, name="resource_availability"),
    path("resources/<int:resource_id>/approve/", views.resource_approve, name="resource_approve"),
    path("tasks/", views.lecturer_task_list, name="lecturer_task_list"),
    path("tasks/new/", views.task_create, name="task_create"),
    path("tasks/<int:task_id>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:task_id>/publish/", views.task_publish, name="task_publish"),
    path("assigned/", views.student_task_list, name="student_task_list"),
    path("assigned/<int:task_id>/", views.student_task_detail, name="student_task_detail"),
    path("assigned/<int:task_id>/start/", views.submission_start, name="submission_start"),
    path("submissions/<int:submission_id>/", views.submission_workspace, name="submission_workspace"),
    path("submissions/<int:submission_id>/evidence/add/", views.evidence_add, name="evidence_add"),
    path("submissions/<int:submission_id>/evidence/<int:evidence_id>/remove/", views.evidence_remove, name="evidence_remove"),
    path("submissions/<int:submission_id>/submit/", views.submission_confirm, name="submission_confirm"),
    path("evidence/<int:evidence_id>/download/", views.evidence_download, name="evidence_download"),
    path("review/", views.review_queue, name="review_queue"),
    path("review/<int:submission_id>/", views.submission_review, name="submission_review"),
    path("review/<int:submission_id>/assess/", views.assessment_save, name="assessment_save"),
    path("review/<int:submission_id>/return/", views.submission_return, name="submission_return"),
    path("assessments/<int:assessment_id>/release/", views.result_release, name="result_release"),
    path("results/", views.result_list, name="result_list"),
    path("results/<int:assessment_id>/", views.result_detail, name="result_detail"),
    path("submissions/<int:submission_id>/integration/launch/", views.integration_launch, name="integration_launch"),
    path("integrations/sessions/<uuid:public_id>/", views.integration_status, name="integration_status"),
    path("integrations/return/", views.integration_return, name="integration_return"),
]
