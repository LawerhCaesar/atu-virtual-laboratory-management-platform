"""Student attribution supplied by module handovers; never infer missing identities.

Add approved biography text and a local static portrait path when supplied.
Partial source names remain partial until the student confirms their full name.
"""
MODULE_STUDENTS = {
    "core:ect": {"name": "David Amachie"},
    "core:edward": {"name": "Edward Selorm"},
    "core:p2_hybrid": {"name": "Lawrence Andoh"},
    "core:micro_hybrid": {"name": "Abass Moro"},
    "core:bless": {"name": "Bless", "name_note": "Full name to be confirmed"},
    "core:battery_energy": {"name": "Bernard", "name_note": "Full name to be confirmed"},
    "core:series_parallel": {"name": "Desmond", "name_note": "Full name to be confirmed"},
    "core:engine_live_data": {},
    "core:fuel_delivery": {},
    "core:brakelab": {},
    "core:wheel_slip": {},
    "core:steering_response": {},
    "core:engine_generator": {},
}


def student_profile(route, module_name):
    source = MODULE_STUDENTS.get(route, {})
    return {
        "name": source.get("name", "Student name to be confirmed"),
        "name_note": source.get("name_note", ""),
        "bio": source.get("bio", "A short student biography will be added here once provided."),
        "portrait": source.get("portrait", ""),
        "module_name": module_name,
    }
