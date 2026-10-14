from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Faculty(models.Model):
    name = models.CharField(max_length=160, unique=True)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "faculties"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name="departments")
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["faculty", "name"], name="unique_department_name_per_faculty")]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Programme(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="programmes")
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=24, unique=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["department", "name"], name="unique_programme_name_per_department")]

    def __str__(self):
        return f"{self.name} ({self.code})"


class AcademicProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academic_profile",
    )
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name="profiles")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="profiles")
    programme = models.ForeignKey(
        Programme,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="profiles",
        help_text="Required for students; optional for lecturers.",
    )
    student_or_staff_id = models.CharField(max_length=50, unique=True)
    configured_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="configured_academic_profiles",
    )
    configured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__full_name"]

    def clean(self):
        errors = {}
        if self.department_id and self.department.faculty_id != self.faculty_id:
            errors["department"] = "The department must belong to the selected faculty."
        if self.programme_id and self.programme.department_id != self.department_id:
            errors["programme"] = "The programme must belong to the selected department."
        if self.user_id and self.user.role == self.user.Role.STUDENT and not self.programme_id:
            errors["programme"] = "A programme is required for student accounts."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Academic profile for {self.user}"


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="For example, 2026/2027.")
    starts_on = models.DateField()
    ends_on = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-starts_on"]

    def clean(self):
        if self.starts_on and self.ends_on and self.ends_on <= self.starts_on:
            raise ValidationError({"ends_on": "The academic year must end after it starts."})

    def __str__(self):
        return self.name


class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="courses")
    code = models.CharField(max_length=24, unique=True)
    title = models.CharField(max_length=180)
    credit_hours = models.PositiveSmallIntegerField(default=3)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.title}"


class CourseOffering(models.Model):
    class Semester(models.IntegerChoices):
        FIRST = 1, "First semester"
        SECOND = 2, "Second semester"

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="offerings")
    programme = models.ForeignKey(Programme, on_delete=models.PROTECT, related_name="course_offerings")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="course_offerings")
    semester = models.PositiveSmallIntegerField(choices=Semester.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-academic_year__starts_on", "semester", "course__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "programme", "academic_year", "semester"],
                name="unique_course_offering",
            )
        ]

    def clean(self):
        if self.course_id and self.programme_id:
            if self.course.department_id != self.programme.department_id:
                raise ValidationError(
                    {"course": "The course and programme must belong to the same department."}
                )

    def __str__(self):
        return f"{self.course.code} · {self.academic_year.name} · {self.get_semester_display()}"


class TeachingAssignment(models.Model):
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="teaching_assignments")
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_teaching_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["offering", "lecturer"], name="unique_teaching_assignment")
        ]

    def clean(self):
        if self.lecturer_id and self.lecturer.role != self.lecturer.Role.LECTURER:
            raise ValidationError({"lecturer": "Only Lecturer accounts can be assigned to teach."})

    def __str__(self):
        return f"{self.lecturer} → {self.offering}"


class Enrollment(models.Model):
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="course_enrollments",
    )
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_enrollments",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["offering", "student"], name="unique_enrollment")]

    def clean(self):
        errors = {}
        if self.student_id and self.student.role != self.student.Role.STUDENT:
            errors["student"] = "Only Student accounts can be enrolled."
        if self.student_id and self.offering_id:
            try:
                student_programme_id = self.student.academic_profile.programme_id
            except AcademicProfile.DoesNotExist:
                student_programme_id = None
            if student_programme_id != self.offering.programme_id:
                errors["student"] = "The student's academic profile must match the offering programme."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.student} → {self.offering}"
