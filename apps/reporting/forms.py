from django import forms

from apps.academics.models import CourseOffering
from apps.practicals.models import PracticalSubmission


class SubmissionReportFilterForm(forms.Form):
    offering = forms.ModelChoiceField(queryset=CourseOffering.objects.none(), required=False)
    status = forms.ChoiceField(
        choices=[("", "All statuses"), *PracticalSubmission.Status.choices], required=False
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["offering"].queryset = CourseOffering.objects.select_related(
            "course", "academic_year"
        ).all()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("date_from") and cleaned.get("date_to"):
            if cleaned["date_to"] < cleaned["date_from"]:
                self.add_error("date_to", "The end date cannot be earlier than the start date.")
        return cleaned


class AuditFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Actor or target")
    action = forms.ChoiceField(required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, actions=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["action"].choices = [("", "All actions"), *((value, value.replace("_", " ").title()) for value in actions)]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("date_from") and cleaned.get("date_to"):
            if cleaned["date_to"] < cleaned["date_from"]:
                self.add_error("date_to", "The end date cannot be earlier than the start date.")
        return cleaned

