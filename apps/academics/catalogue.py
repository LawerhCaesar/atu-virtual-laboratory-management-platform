"""Reviewed ATU choices for registration; these never grant academic access."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def registration_catalogue():
    return json.loads((Path(__file__).parent / "data/atu_catalogue_2026_2027.json").read_text())


def selection_snapshot(faculty_id, department_id, programme_id=""):
    catalogue = registration_catalogue()
    faculty = next(f for f in catalogue["faculties"] if f["id"] == faculty_id)
    department = next(d for d in catalogue["departments"] if d["id"] == department_id)
    programme = next((p for p in catalogue["programmes"] if p["id"] == programme_id), None)
    return {
        "faculty_id": faculty_id, "department_id": department_id,
        "programme_id": programme_id or "", "faculty": faculty["name"],
        "department": department["name"], "programme": programme["name"] if programme else "",
        "catalogue_reviewed_on": catalogue["reviewed_on"],
        "department_confirmation_required": bool(programme and not programme["department_confirmed"]),
    }


def prepare_requested_structure(user):
    """Run only inside the administrator's approval transaction, never on GET.

    Add the requested verified structure without renaming existing records.
    Unconfirmed programme associations remain for the administrator to configure.
    """
    from .models import Department, Faculty, Programme
    request = user.registration_academics
    if not request:
        return {}
    try:
        selection = selection_snapshot(request["faculty_id"], request["department_id"], request.get("programme_id"))
    except (KeyError, StopIteration):
        return {}
    faculty, _ = Faculty.objects.get_or_create(
        name=selection["faculty"], defaults={"code": "ATU-" + request["faculty_id"][:16].upper()},
    )
    department, _ = Department.objects.get_or_create(
        faculty=faculty, name=selection["department"],
        defaults={"code": "ATU-" + request["department_id"][:16].upper()},
    )
    result = {"faculty": faculty.pk, "department": department.pk}
    if selection["programme"] and not selection["department_confirmation_required"]:
        import hashlib
        code = "ATU-" + hashlib.sha256(request["programme_id"].encode()).hexdigest()[:16].upper()
        programme, _ = Programme.objects.get_or_create(
            department=department, name=selection["programme"], defaults={"code": code},
        )
        result["programme"] = programme.pk
    return result


def requested_structure_initial(user):
    """Prefill only records already available for an administrator to confirm."""
    from .models import Department, Faculty, Programme
    selection = user.registration_academics
    if not selection:
        return {}
    faculty = Faculty.objects.filter(name=selection.get("faculty")).first()
    if not faculty:
        return {}
    department = Department.objects.filter(faculty=faculty, name=selection.get("department")).first()
    if not department:
        return {"faculty": faculty.pk}
    initial = {"faculty": faculty.pk, "department": department.pk}
    if not selection.get("department_confirmation_required"):
        programme = Programme.objects.filter(department=department, name=selection.get("programme")).first()
        if programme:
            initial["programme"] = programme.pk
    return initial
