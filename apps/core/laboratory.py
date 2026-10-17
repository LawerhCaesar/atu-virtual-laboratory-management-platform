"""System catalogue; only implemented models receive simulation launch links."""

SYSTEMS = (
    {"slug": "ice", "code": "ICE", "name": "Internal Combustion Engine",
     "tagline": "From sensor input to engine response.",
     "description": "Explore combustion-engine management, fuel delivery, ignition and thermal control."},
    {"slug": "bev", "code": "BEV", "name": "Battery Electric Vehicle",
     "tagline": "Electrical energy. Electric motion.",
     "description": "The Battery Electric Vehicle laboratory environment."},
    {"slug": "fcev", "code": "FCEV", "name": "Fuel Cell Electric Vehicle",
     "tagline": "Hydrogen to electrical power.",
     "description": "The Fuel Cell Electric Vehicle laboratory environment."},
    {"slug": "hybrid", "code": "HEV", "name": "Hybrid Electric Vehicle",
     "tagline": "Two power sources. One coordinated drive.",
     "description": "The Hybrid Electric Vehicle laboratory environment."},
    {"slug": "vehicle-dynamics", "code": "VD", "name": "Vehicle Dynamics",
     "tagline": "Understand motion, grip and stability.",
     "description": "The Vehicle Dynamics laboratory environment."},
)

ICE_MODELS = (
    {"key": "fuel", "title": "Fuel and injection", "description": "Oxygen feedback, fuel correction and injector pulse width."},
    {"key": "idle", "title": "Idle and ignition", "description": "Target idle, RPM error and commanded ignition timing."},
    {"key": "cooling", "title": "Cooling", "description": "Virtual temperature sensors, fan duty and electric-water-pump duty."},
    {"key": "startRun", "title": "Start and run", "description": "Authorisation, priming, cranking, running and shutdown."},
)
