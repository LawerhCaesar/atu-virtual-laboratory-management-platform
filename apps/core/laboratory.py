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

ENGINE_MODEL_NAME = "Engine Live Data Demonstration"
ENGINE_VIEW_KEYS = frozenset({"fuel", "idle", "cooling", "startRun"})

ICE_MODELS = (
    # Engine Live Data Demonstration is temporarily withdrawn; its source is retained.
    {"title": "Fuel Delivery Optimisation", "route_name": "core:fuel_delivery",
     "description": "Explore injector delivery, fuel trims and consumption with an interactive fuel path, time-series plots and baseline comparison."},
)

BEV_MODELS = (
    {"title": "Regenerative and Friction Brake-Force Allocation", "route_name": "core:brakelab",
     "description": "BrakeLab: adjust vehicle, battery and motor inputs to explore braking allocation, limiting conditions and an illustrative energy-flow vehicle."},
)
VEHICLE_DYNAMICS_MODELS = (
    {"title": "Wheel-Slip Control Using ABS and TCS", "route_name": "core:wheel_slip",
     "description": "Investigate wheel slip, road grip and controller response in braking and acceleration."},
    {"title": "Vehicle Steering Response", "route_name": "core:steering_response",
     "description": "Explore lateral-yaw response, tyre forces and a calculated X-Y vehicle trajectory."},
)
HYBRID_MODELS = (
    {"title": "12 V Micro-Hybrid Stop-Start", "route_name": "core:micro_hybrid",
     "description": "Compare conventional idling with stop-start fuel use and explore battery and restart constraints."},
)
SYSTEM_MODELS = {"ice": ICE_MODELS, "bev": BEV_MODELS, "hybrid": HYBRID_MODELS, "vehicle-dynamics": VEHICLE_DYNAMICS_MODELS}
