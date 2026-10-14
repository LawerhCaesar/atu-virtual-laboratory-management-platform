from django.contrib import admin

from .models import (
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


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "faculty")
    list_filter = ("faculty",)
    search_fields = ("name", "code")


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "department")
    list_filter = ("department__faculty", "department")
    search_fields = ("name", "code")


@admin.register(AcademicProfile)
class AcademicProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "student_or_staff_id", "faculty", "department", "programme")
    search_fields = ("user__email", "user__full_name", "student_or_staff_id")


admin.site.register(AcademicYear)
admin.site.register(Course)
admin.site.register(CourseOffering)
admin.site.register(TeachingAssignment)
admin.site.register(Enrollment)
