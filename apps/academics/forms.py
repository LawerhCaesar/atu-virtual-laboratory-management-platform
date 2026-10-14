from django import forms

from apps.accounts.models import User

from .models import AcademicProfile, Course, CourseOffering


class AcademicSetupForm(forms.ModelForm):
    class Meta:
        model = AcademicProfile
        fields = ("faculty", "department", "programme", "student_or_staff_id")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user.role == user.Role.LECTURER:
            self.fields["programme"].required = False

    def clean(self):
        cleaned = super().clean()
        faculty = cleaned.get("faculty")
        department = cleaned.get("department")
        programme = cleaned.get("programme")
        if faculty and department and department.faculty_id != faculty.pk:
            self.add_error("department", "Select a department within the chosen faculty.")
        if department and programme and programme.department_id != department.pk:
            self.add_error("programme", "Select a programme within the chosen department.")
        if self.user.role == self.user.Role.STUDENT and not programme:
            self.add_error("programme", "A programme is required for a student.")
        return cleaned


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("department", "code", "title", "credit_hours", "is_active")

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()


class CourseOfferingForm(forms.ModelForm):
    class Meta:
        model = CourseOffering
        fields = ("course", "programme", "academic_year", "semester", "is_active")


class OfferingAccessForm(forms.Form):
    lecturers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, offering, **kwargs):
        super().__init__(*args, **kwargs)
        self.offering = offering
        self.fields["lecturers"].queryset = User.objects.filter(
            role=User.Role.LECTURER,
            approval_status=User.ApprovalStatus.ACTIVE,
            academic_profile__department=offering.programme.department,
        ).order_by("full_name")
        self.fields["students"].queryset = User.objects.filter(
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.ACTIVE,
            academic_profile__programme=offering.programme,
        ).order_by("full_name")
        if not self.is_bound:
            self.initial["lecturers"] = offering.teaching_assignments.filter(
                is_active=True
            ).values_list("lecturer_id", flat=True)
            self.initial["students"] = offering.enrollments.filter(is_active=True).values_list(
                "student_id", flat=True
            )
