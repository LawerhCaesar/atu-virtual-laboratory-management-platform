from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.functions import Length
from django.db.models.lookups import Exact
from .identifiers import normalise_index, validate_student_index
from django.utils.crypto import salted_hmac


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, identifier):
        identifier = str(identifier).strip()
        if "@" in identifier:
            return self.get(email__iexact=identifier)
        return self.get(index_number__iexact=identifier)

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMINISTRATOR)
        extra_fields.setdefault("approval_status", User.ApprovalStatus.ACTIVE)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMINISTRATOR = "ADMIN", "Administrator"
        LECTURER = "LECTURER", "Lecturer"
        STUDENT = "STUDENT", "Student"

    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending approval"
        ACADEMIC_SETUP = "ACADEMIC_SETUP", "Academic setup required"
        ACTIVE = "ACTIVE", "Active"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    class Qualification(models.TextChoices):
        HND = "HND", "HND"
        BTECH = "BTECH", "BTECH"
        MTECH = "MTECH", "MTECH"

    username = None
    index_number = models.CharField(max_length=9, unique=True, null=True, blank=True, verbose_name="index number")
    qualification = models.CharField(max_length=5, choices=Qualification.choices, blank=True, default="", verbose_name="course")
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=180)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT)
    approval_status = models.CharField(
        max_length=24,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
    )
    must_change_password = models.BooleanField(default=False)
    session_revision = models.PositiveIntegerField(default=0)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_accounts",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        ordering = ["full_name", "email"]
        constraints = [models.CheckConstraint(
            condition=(
                models.Q(index_number__isnull=True, qualification="")
                | (models.Q(index_number__isnull=False, role="STUDENT")
                   & Exact(Length("index_number"), 9)
                   & (models.Q(qualification="HND", index_number__regex=r"^[0-9]{8}D$")
                      | models.Q(qualification="BTECH", index_number__regex=r"^[0-9]{8}B$")
                      | models.Q(qualification="MTECH", index_number__regex=r"^[0-9]{8}M$")))
            ), name="valid_student_index_course",
        )]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def clean(self):
        super().clean()
        self.index_number = normalise_index(self.index_number)
        if self.index_number or self.qualification:
            if self.role != self.Role.STUDENT:
                raise ValidationError({"index_number": "Index usernames apply to student accounts."})
            try:
                validate_student_index(self.index_number, self.qualification)
            except ValidationError as error:
                raise ValidationError({"index_number": error.messages})

    def save(self, *args, **kwargs):
        self.index_number = normalise_index(self.index_number)
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def is_platform_active(self):
        return self.is_active and self.approval_status == self.ApprovalStatus.ACTIVE

    def _get_session_auth_hash(self, secret=None):
        return salted_hmac(
            "accounts.User.session_revision",
            f"{self.password}:{self.session_revision}",
            secret=secret,
            algorithm="sha256",
        ).hexdigest()
