from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import User
from apps.academics.models import (
    AcademicProfile,
    AcademicYear,
    Course,
    CourseOffering,
    Department,
    Enrollment,
    Faculty,
    Programme,
    TeachingAssignment,
)
from apps.practicals.models import ApprovedResource, EvidenceFile, PracticalSubmission, PracticalTask


class Command(BaseCommand):
    help = "Create idempotent local demonstration data without grades or results."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demonstration data can only be created when DJANGO_DEBUG=true.")

        administrator = self._user(
            email="admin@atu-demo.local",
            full_name="Demo Administrator",
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
            is_superuser=True,
        )
        lecturer = self._user(
            email="lecturer@atu-demo.local",
            full_name="Demo Lecturer",
            role=User.Role.LECTURER,
        )
        student = self._user(
            email="student@atu-demo.local",
            full_name="Demo Student",
            role=User.Role.STUDENT,
        )
        review_student = self._user(
            email="review-student@atu-demo.local",
            full_name="Demo Review Student",
            role=User.Role.STUDENT,
        )

        faculty, _ = Faculty.objects.get_or_create(
            code="FOE", defaults={"name": "Faculty of Engineering"}
        )
        department, _ = Department.objects.get_or_create(
            code="AUTO",
            defaults={"name": "Automotive Engineering Department", "faculty": faculty},
        )
        programme, _ = Programme.objects.get_or_create(
            code="MTECH-AUTO",
            defaults={"name": "MTech Automotive Engineering", "department": department},
        )
        self._profile(lecturer, faculty, department, None, "DEMO-STAFF-001", administrator)
        self._profile(student, faculty, department, programme, "DEMO-STUDENT-001", administrator)
        self._profile(
            review_student,
            faculty,
            department,
            programme,
            "DEMO-STUDENT-002",
            administrator,
        )

        today = timezone.localdate()
        year, _ = AcademicYear.objects.get_or_create(
            name="2026/2027",
            defaults={"starts_on": today, "ends_on": today + timedelta(days=300), "is_current": True},
        )
        course, _ = Course.objects.get_or_create(
            code="AUTO 701",
            defaults={
                "department": department,
                "title": "Automotive Systems Diagnostics",
                "credit_hours": 3,
            },
        )
        offering, _ = CourseOffering.objects.get_or_create(
            course=course,
            programme=programme,
            academic_year=year,
            semester=CourseOffering.Semester.FIRST,
        )
        TeachingAssignment.objects.update_or_create(
            offering=offering,
            lecturer=lecturer,
            defaults={"assigned_by": administrator, "is_active": True},
        )
        Enrollment.objects.update_or_create(
            offering=offering,
            student=student,
            defaults={"enrolled_by": administrator, "is_active": True},
        )
        Enrollment.objects.update_or_create(
            offering=offering,
            student=review_student,
            defaults={"enrolled_by": administrator, "is_active": True},
        )
        resource, _ = ApprovedResource.objects.update_or_create(
            title="Approved vehicle diagnostics demonstration",
            defaults={
                "description": "Placeholder controlled link for local workflow demonstration.",
                "url": "https://example.com/",
                "version_label": "demo-v1",
                "status": ApprovedResource.Status.APPROVED,
                "created_by": administrator,
                "approved_by": administrator,
                "approved_at": timezone.now(),
            },
        )
        task, _ = PracticalTask.objects.update_or_create(
            offering=offering,
            title="Interpret a structured diagnostic parameter set",
            defaults={
                "instructions": "Review the approved demonstration and follow the stated practical procedure.",
                "question": "Explain how the supplied parameters support a structured automotive diagnostic decision.",
                "evidence_requirements": "Provide a parameter summary and one clearly labelled plot.",
                "due_at": timezone.now() + timedelta(days=14),
                "max_score": 100,
                "max_resubmissions": 1,
                "status": PracticalTask.Status.PUBLISHED,
                "created_by": lecturer,
                "published_at": timezone.now(),
            },
        )
        task.resources.set([resource])
        PracticalSubmission.objects.get_or_create(
            task=task,
            student=student,
            attempt_number=1,
            defaults={
                "status": PracticalSubmission.Status.DRAFT,
                "response_text": "Draft explanation of the diagnostic parameter relationship.",
                "resource": resource,
                "parameter_summary": "Record the parameters used during the demonstration.",
                "run_session_id": "DEMO-RUN-001",
                "run_status": PracticalSubmission.RunStatus.COMPLETED,
                "output_summary": "Describe the observed output before confirming submission.",
            },
        )
        review_submission, _ = PracticalSubmission.objects.update_or_create(
            task=task,
            student=review_student,
            attempt_number=1,
            defaults={
                "status": PracticalSubmission.Status.SUBMITTED,
                "response_text": "Demonstration response awaiting Lecturer assessment.",
                "resource": resource,
                "resource_version": resource.version_label,
                "parameter_summary": "engine_speed=1500 rpm; vehicle_speed=30 km/h",
                "run_session_id": "DEMO-REVIEW-001",
                "run_status": PracticalSubmission.RunStatus.COMPLETED,
                "output_summary": "A labelled output plot was generated for review.",
                "submitted_at": timezone.now(),
            },
        )
        if not review_submission.evidence_files.exists():
            demo_evidence = b"Demo parameter evidence for interface review.\n"
            EvidenceFile.objects.create(
                submission=review_submission,
                file=ContentFile(demo_evidence, name="demo-evidence.txt"),
                original_name="demo-evidence.txt",
                content_type="text/plain",
                size_bytes=len(demo_evidence),
            )

        self.stdout.write(self.style.SUCCESS("Local demonstration data is ready."))
        self.stdout.write("Password for all demo accounts: DemoPass!742")
        self.stdout.write("Administrator: admin@atu-demo.local")
        self.stdout.write("Lecturer: lecturer@atu-demo.local")
        self.stdout.write("Student: student@atu-demo.local")
        self.stdout.write("Review student: review-student@atu-demo.local")

    def _user(self, *, email, full_name, role, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "role": role,
                "approval_status": User.ApprovalStatus.ACTIVE,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        if created:
            user.set_password("DemoPass!742")
            user.save(update_fields=["password"])
        return user

    def _profile(self, user, faculty, department, programme, identifier, administrator):
        AcademicProfile.objects.update_or_create(
            user=user,
            defaults={
                "faculty": faculty,
                "department": department,
                "programme": programme,
                "student_or_staff_id": identifier,
                "configured_by": administrator,
            },
        )
