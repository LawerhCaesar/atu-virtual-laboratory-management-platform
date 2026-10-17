"""System catalogue; only implemented models receive simulation launch links."""

SYSTEMS = (
    {"slug": "ice", "code": "ICE", "name": "Internal Combustion Engine",
     "tagline": "From sensor input to engine response.",
     "description": "Explore combustion-engine management, fuel delivery, ignition and thermal control.",
     "topics": ("Fuel and injection", "Idle and ignition", "Cooling", "Start and run")},
    {"slug": "bev", "code": "BEV", "name": "Battery Electric Vehicle",
     "tagline": "Electrical energy. Electric motion.",
     "description": "A dedicated environment for battery storage, electric traction and charging studies.",
     "topics": ("Battery behaviour", "Electric traction", "Charging and energy management")},
    {"slug": "fcev", "code": "FCEV", "name": "Fuel Cell Electric Vehicle",
     "tagline": "Hydrogen to electrical power.",
     "description": "A dedicated environment for fuel-cell generation, hydrogen supply and electric propulsion studies.",
     "topics": ("Fuel-cell stack", "Hydrogen supply", "Electrical energy management")},
    {"slug": "hybrid", "code": "HEV", "name": "Hybrid Electric Vehicle",
     "tagline": "Two power sources. One coordinated drive.",
     "description": "A dedicated environment for engine–motor coordination and hybrid energy-flow studies.",
     "topics": ("Power split", "Operating modes", "Regenerative braking")},
    {"slug": "vehicle-dynamics", "code": "VD", "name": "Vehicle Dynamics",
     "tagline": "Understand motion, grip and stability.",
     "description": "A dedicated environment for vehicle motion, tyre interaction and handling studies across powertrains.",
     "topics": ("Longitudinal motion", "Lateral handling", "Ride and suspension")},
)

ICE_MODELS = (
    {"key": "fuel", "title": "Fuel and injection", "description": "Oxygen feedback, fuel correction and injector pulse width."},
    {"key": "idle", "title": "Idle and ignition", "description": "Target idle, RPM error and commanded ignition timing."},
    {"key": "cooling", "title": "Cooling", "description": "Virtual temperature sensors, fan duty and electric-water-pump duty."},
    {"key": "startRun", "title": "Start and run", "description": "Authorisation, priming, cranking, running and shutdown."},
)
