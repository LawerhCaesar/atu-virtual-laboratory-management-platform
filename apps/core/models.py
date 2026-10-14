from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from urllib.parse import unquote, urlsplit


def is_internal_link(value):
    decoded = unquote(value)
    return (
        decoded.startswith("/") and not decoded.startswith("//")
        and "\\" not in decoded and not any(ord(char) < 32 for char in decoded)
        and not urlsplit(decoded).netloc and not urlsplit(decoded).scheme
    )


class PlatformSettings(models.Model):
    """Educational/support settings only; deployment secrets stay outside the DB."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    support_email = models.EmailField(blank=True)
    support_hours = models.CharField(max_length=180, blank=True)
    help_message = models.TextField(max_length=4000, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.pk != 1:
            raise ValidationError("Only one platform settings record is permitted.")


class AdministratorNotice(models.Model):
    class Audience(models.TextChoices):
        ALL = "ALL", "All active Students and Lecturers"
        STUDENT = "STUDENT", "Active Students"
        LECTURER = "LECTURER", "Active Lecturers"
        INDIVIDUAL = "INDIVIDUAL", "One active Student or Lecturer"

    title = models.CharField(max_length=180)
    message = models.TextField(max_length=4000)
    link = models.CharField(max_length=300, blank=True)
    audience = models.CharField(max_length=16, choices=Audience.choices)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="targeted_notices")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="administrator_notices")
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def clean(self):
        if self.link and not is_internal_link(self.link):
            raise ValidationError({"link": "Use a single-slash internal platform path."})
        if self.audience == self.Audience.INDIVIDUAL and not self.recipient_id:
            raise ValidationError({"recipient": "Select an active account for an individual notice."})
        if self.audience != self.Audience.INDIVIDUAL and self.recipient_id:
            raise ValidationError({"recipient": "Leave recipient empty for a role-wide notice."})


class SupportRequest(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESOLVED = "RESOLVED", "Resolved"

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="support_requests")
    subject = models.CharField(max_length=180)
    message = models.TextField(max_length=4000)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    response = models.TextField(max_length=4000, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="reviewed_support_requests")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]


class Notification(models.Model):
    class Category(models.TextChoices):
        TASK = "TASK", "Practical task"
        RESUBMISSION = "RESUBMISSION", "Resubmission"
        RESULT = "RESULT", "Result"
        SYSTEM = "SYSTEM", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=180)
    message = models.TextField()
    link = models.CharField(max_length=300, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    notice = models.ForeignKey(AdministratorNotice, null=True, blank=True, on_delete=models.PROTECT, related_name="deliveries")

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["notice", "recipient"], name="unique_notice_delivery_per_recipient")]

    def clean(self):
        if self.link and not is_internal_link(self.link):
            raise ValidationError({"link": "Notification links must be internal platform paths."})

    def __str__(self):
        return f"{self.title} → {self.recipient}"
