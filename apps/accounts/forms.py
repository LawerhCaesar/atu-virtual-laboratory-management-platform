from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class AccountAvailabilityForm(forms.Form):
    reason = forms.CharField(max_length=500, widget=forms.Textarea, help_text="Record the administrative reason without passwords or sensitive evidence.")
    confirm = forms.BooleanField(label="I confirm this account-access change. Existing sessions will be revoked; academic records are retained.")


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (User.Role.STUDENT, User.Role.STUDENT.label),
            (User.Role.LECTURER, User.Role.LECTURER.label),
        ]
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "role")

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
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
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
