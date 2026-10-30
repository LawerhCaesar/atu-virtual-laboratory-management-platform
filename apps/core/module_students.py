"""Student attribution supplied by module handovers; never infer missing identities.

Add approved biography text and a local static portrait path when supplied.
Partial source names remain partial until the student confirms their full name.
"""
MODULE_STUDENTS = {
    "core:yankson": {"name": "Emmanuel Yankson Sackey", "show_bio": False, "show_portrait": False},
    "core:ect": {"name": "David Amachie"},
    "core:edward": {"name": "Edward Selorm"},
    "core:p2_hybrid": {"name": "Lawrence Andoh", "bio": "Lawrence Andoh, Master of Automotive Engineering researcher at Accra Technical University specializing in hybrid electric powertrain modeling and battery energy management. Focuses on optimizing energy consumption, torque-split dynamics, and battery storage efficiency across varying load profiles in full parallel hybrid architectures."},
    "core:micro_hybrid": {"name": "Abass Moro"},
    "core:bless": {"name": "Bless", "name_note": "Full name to be confirmed"},
    "core:battery_energy": {"name": "Bernard", "name_note": "Full name to be confirmed"},
    "core:series_parallel": {"name": "Desmond", "name_note": "Full name to be confirmed"},
    "core:engine_live_data": {},
    "core:fuel_delivery": {},
    "core:brakelab": {"name": "Ebenezer Wilson", "bio": 'Ebenezer Wilson is a versatile automotive and mechanical engineering professional with a diverse background in vehicle maintenance, plant operation, driving, data entry, real estate, military intelligence, and military service. He began his career as a mechanic with Hajime Shokai before progressing into plant operation. He subsequently gained experience with Najafs Rentals and Adom Estate, as well as working as a Data Entry Clerk with JH Micro Finance. He later joined the Ghana Armed Forces as an Infantry Soldier, choosing vehicle maintenance and driving as his trades while also developing expertise in military intelligence.\n\nHis diverse professional experience has equipped him with practical technical skills, operational competence, analytical thinking, discipline, adaptability, and a strong sense of responsibility.\n\nHis professional interests include automotive and mechanical engineering, vehicle maintenance and diagnostics, fleet management, plant operations, military intelligence, and engineering innovation. He is committed to continuous professional development, effective leadership, problem-solving, and applying his technical and analytical expertise to improve operational efficiency and organisational performance.'},
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
        "show_bio": source.get("show_bio", True),
        "show_portrait": source.get("show_portrait", True),
        "module_name": module_name,
    }
