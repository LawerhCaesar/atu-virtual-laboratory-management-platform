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
    "core:wheel_slip": {
        "name": "Abubakar Sadiq Ibrahim",
        "bio": (
            "Abubakar Sadiq Ibrahim is a Ghanaian engineering graduate with a strong academic background in Automobile and Mechanical Engineering and a keen interest in advancing his knowledge and expertise in the automotive industry.\n\n"
            "He holds a Bachelor of Technology (BTech) degree in Automobile Engineering and a Higher National Diploma (HND) in Mechanical Engineering, both from Accra Technical University, Ghana. His academic journey has provided him with a solid foundation in automotive systems, mechanical principles, vehicle maintenance, diagnostics, and engineering technology.\n\n"
            "Beyond his academic qualifications, Abubakar has acquired valuable practical experience in automobile maintenance, vehicle inspection, troubleshooting, repairs, and industrial equipment maintenance. Through his professional experience with the Ghana Standards Authority, he has developed practical skills in vehicle servicing, fault diagnosis, maintenance procedures, and technical record management.\n\n"
            "He also gained six months of experience in the Asset Maintenance Department at Meridian Port Services (MPS), where he worked in Rolling Stock Maintenance, handling equipment such as reach stackers, empty handlers, and forklifts. This experience strengthened his understanding of heavy equipment maintenance, mechanical systems, workplace safety, and industrial maintenance operations. He also completed the Lean Onboarding Programme at Meridian Port Services and received a certificate in recognition of his participation.\n\n"
            "Furthermore, his professional training at West African Vehicles Academy (WAVA), where he obtained certificates in Service Advisory and Automotive Air Conditioning Systems, has contributed to his technical and professional development.\n\n"
            "Abubakar is passionate about continuous learning, engineering innovation, automotive technology, and the development of efficient and sustainable vehicle systems. He is particularly interested in deepening his knowledge of advanced automotive engineering, vehicle diagnostics, maintenance technologies, and emerging developments in the automotive sector.\n\n"
            "His ambition to pursue a Master’s degree in Automobile Engineering is driven by his desire to acquire advanced technical knowledge, strengthen his research and problem-solving abilities, and develop the expertise required to contribute to technological advancement and innovation in the automotive industry.\n\n"
            "He considers postgraduate education an important step towards achieving his long-term professional goals of becoming a highly skilled engineering professional and contributing meaningfully to the development of the automobile engineering sector in Ghana and beyond."
        ),
    },
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
