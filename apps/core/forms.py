from django import forms
from django.urls import Resolver404, resolve

from apps.accounts.models import User
from .models import AdministratorNotice, PlatformSettings, SupportRequest, is_internal_link


class PlatformSettingsForm(forms.ModelForm):
    class Meta:
        model = PlatformSettings
        fields = ["support_email", "support_hours", "help_message"]
        help_texts = {"help_message": "Plain-text guidance only. Never enter passwords, shared secrets or private student records."}


class AdministratorNoticeForm(forms.ModelForm):
    class Meta:
        model = AdministratorNotice
        fields = ["title", "message", "audience", "recipient", "link"]
        help_texts = {"link": "Optional existing platform path, for example /help/. Access permissions still apply.", "recipient": "Only needed for an individual notice."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipient"].queryset = User.objects.filter(is_active=True, approval_status=User.ApprovalStatus.ACTIVE).exclude(role=User.Role.ADMINISTRATOR)

    def clean_link(self):
        link = self.cleaned_data["link"]
        if link:
            if not is_internal_link(link):
                raise forms.ValidationError("Use a single-slash internal platform path.")
            try:
                resolve(link.split("?", 1)[0].split("#", 1)[0])
            except Resolver404:
                raise forms.ValidationError("This platform path does not exist.")
        return link


class SupportRequestForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = ["subject", "message"]
        help_texts = {"message": "Describe the problem without passwords or sensitive evidence. This is platform support, not research-study feedback."}


class SupportResponseForm(forms.ModelForm):
    response = forms.CharField(max_length=4000, widget=forms.Textarea)

    class Meta:
        model = SupportRequest
        fields = ["status", "response"]
