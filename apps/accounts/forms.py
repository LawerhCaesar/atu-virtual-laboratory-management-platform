from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User
from .identifiers import normalise_index, validate_student_index


class AccountAvailabilityForm(forms.Form):
    reason = forms.CharField(max_length=500, widget=forms.Textarea, help_text="Record the administrative reason without passwords or sensitive evidence.")
    confirm = forms.BooleanField(label="I confirm this account-access change. Existing sessions will be revoked; academic records are retained.")


class RegistrationForm(UserCreationForm):
    qualification = forms.ChoiceField(label="Course", choices=[("", "Select your course"), *User.Qualification.choices], required=False,
        help_text="Students: HND ends in D, BTECH in B, MTECH in M.")
    index_number = forms.CharField(label="Username (index number)", required=False, max_length=9,
        widget=forms.TextInput(attrs={"maxlength": "9", "minlength": "9", "pattern": "[0-9]{8}[DBM]", "autocomplete": "username", "autocapitalize": "characters", "spellcheck": "false"}),
        help_text="Exactly 8 digits and your course letter: 01181429D, 01181429B or 01181429M.")

    role = forms.ChoiceField(
        choices=[
            (User.Role.STUDENT, User.Role.STUDENT.label),
            (User.Role.LECTURER, User.Role.LECTURER.label),
        ]
    )

    class Meta:
        model = User
        fields = ("full_name", "role", "qualification", "index_number", "email")

    def clean_index_number(self):
        value = normalise_index(self.cleaned_data.get("index_number"))
        if value:
            from apps.academics.models import AcademicProfile
            if User.objects.filter(index_number__iexact=value).exists() or AcademicProfile.objects.filter(student_or_staff_id__iexact=value).exists():
                raise forms.ValidationError("This index number is already assigned to an account.")
        return value

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("role") == User.Role.STUDENT:
            if not cleaned.get("qualification"):
                self.add_error("qualification", "Select your course: HND, BTECH or MTECH.")
            if "index_number" not in self.errors:
                try:
                    validate_student_index(cleaned.get("index_number"), cleaned.get("qualification"))
                except forms.ValidationError as error:
                    self.add_error("index_number", error)
        elif cleaned.get("role") == User.Role.LECTURER:
            cleaned["index_number"] = None
            cleaned["qualification"] = ""
        return cleaned

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role not in {User.Role.STUDENT, User.Role.LECTURER}:
            raise forms.ValidationError("Only student and lecturer registration is available.")
        return role

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.approval_status = User.ApprovalStatus.PENDING
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class ApprovedAuthenticationForm(AuthenticationForm):
    error_messages = {**AuthenticationForm.error_messages, "invalid_login": "Enter a valid email address or index number and password."}
    username = forms.CharField(
        label="Email address or index number", max_length=254,
        widget=forms.TextInput(attrs={"autocomplete": "username"}),
        help_text="Students may use their 9-character index username. Email sign-in is available for every account.",
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        status_messages = {
            User.ApprovalStatus.PENDING: "Your account is awaiting administrator approval.",
            User.ApprovalStatus.ACADEMIC_SETUP: "Your academic setup is not yet complete.",
            User.ApprovalStatus.REJECTED: "This registration was not approved.",
            User.ApprovalStatus.SUSPENDED: "This account has been suspended.",
        }
        if user.approval_status != User.ApprovalStatus.ACTIVE:
            raise forms.ValidationError(
                status_messages.get(user.approval_status, "This account is not available."),
                code="inactive_platform_account",
            )


class UserManagementFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Name, email or academic ID")
    role = forms.ChoiceField(
        required=False,
        choices=[("", "All roles"), (User.Role.LECTURER, "Lecturer"), (User.Role.STUDENT, "Student")],
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses"), *User.ApprovalStatus.choices],
    )
