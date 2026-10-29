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
    {"title": "Authenticated Engine Starting", "route_name": "core:yankson", "description": "Emmanuel Yankson Sackey: explore simulated fingerprint contacts, authorized voice starting and starter supervision."},
    {"title": "Engine Coolant Temperature Sensor", "route_name": "core:ect",
     "description": "Amachie ECT: explore thermal lag, thermistor resistance, ADC conversion and ECU temperature reconstruction."},
    {"title": ENGINE_MODEL_NAME, "route_name": "core:engine_live_data",
     "description": "Explore virtual fuel, idle, cooling and start/run signals with a shared engine model and visualisation."},
    {"title": "Fuel Delivery Optimisation", "route_name": "core:fuel_delivery",
     "description": "Explore injector delivery, fuel trims and consumption with an interactive fuel path, time-series plots and baseline comparison."},
)

BEV_MODELS = (
    {"title": "Electric Motor Drive and Power Conversion", "route_name": "core:edward",
     "description": "Edward Selorm: explore PMSM control, inverter PWM and independent buck, boost and rectifier experiments."},
    {"title": "Battery Energy Management", "route_name": "core:battery_energy",
     "description": "Explore charging, load supply, thermal limits and SOC with a fixed-step battery model and live energy-flow cutaway."},
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
    {"title": "Series–Parallel Hybrid", "route_name": "core:series_parallel", "description": "Explore supervisory modes, mechanical and electrical power paths, SOC and fuel use."},
    {"title": "Engine–Generator Fuel-to-Electric", "route_name": "core:engine_generator",
     "description": "Explore fuel conversion, generator response, component maps, losses and electrical shortfall in a series-hybrid energy path."},
    {"title": "P2 Full-Parallel Hybrid", "route_name": "core:p2_hybrid",
     "description": "Compare torque intensities, engine–motor allocation and battery energy with an animated P2 powertrain."},
    {"title": "12 V Micro-Hybrid Stop-Start", "route_name": "core:micro_hybrid",
     "description": "Compare conventional idling with stop-start fuel use and explore battery and restart constraints."},
)
FCEV_MODELS = (
    {"title": "Fuel-Cell / Battery and Diesel Comparison", "route_name": "core:bless",
     "description": "Bless passenger-van study: explore battery limits, hydrogen energy, regeneration and diesel comparison."},
)
SYSTEM_MODELS = {"fcev": FCEV_MODELS, "ice": ICE_MODELS, "bev": BEV_MODELS, "hybrid": HYBRID_MODELS, "vehicle-dynamics": VEHICLE_DYNAMICS_MODELS}
