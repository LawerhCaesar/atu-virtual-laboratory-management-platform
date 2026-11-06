"""One registration-index rule shared by forms and model validation."""
import re
from django.core.exceptions import ValidationError

INDEX_SUFFIXES = {"HND": "D", "BTECH": "B", "MTECH": "M"}


def normalise_index(value):
    return str(value or "").strip().upper() or None


def validate_student_index(value, qualification):
    suffix = INDEX_SUFFIXES.get(qualification)
    if not suffix:
        raise ValidationError("Select HND, BTECH or MTECH before entering your index number.")
    if not value or not re.fullmatch(r"[0-9]{8}" + suffix, value):
        raise ValidationError(
            f"Enter exactly 8 digits followed by {suffix} for {qualification} "
            f"(9 characters, for example 01181429{suffix})."
        )
