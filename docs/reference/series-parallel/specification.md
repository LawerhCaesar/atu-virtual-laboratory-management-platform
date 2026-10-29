# AGENTS.md — Series-Parallel Hybrid Virtual-Platform Integration

## 1. Mission
You are Codex working inside the existing virtual-platform repository. Convert the approved MATLAB/Simulink concept into maintainable platform code and integrate it into a user-friendly interface.
The software must reproduce the tested logic of the model named:
`Series_Parallel_Hybrid_All_In_One_Fixed.slx`
The academic project title is:
**Modelling and Testing State-Machine Supervisory Control of Series-Parallel Hybrid Vehicle Operating Modes for Virtual-Platform Integration**
The finished platform module must let a learner or researcher change model parameters, run a deterministic simulation, see the active operating mode and power flow, inspect graphs with visible legends, compare energy paths, and export results.
This is a software port of a control-oriented academic model. It is not an OEM production controller and must never be presented as safe for direct control of a real vehicle.

## 2. Context and sources of truth
Use the following sources in this order:
1. `reference/Series_Parallel_Hybrid_All_In_One_Fixed.slx`
2. `reference/Series_Parallel_Hybrid_Model_Data_and_Operating_Guide_Fixed.docx`
3. `reference/Desmond_Hybrid_Revised_1_3.docx` or the equivalent final thesis document
4. This `AGENTS.md`
5. Optional shared-chat context:
`CHAT_CONTEXT_URL = "PASTE_SHARED_CHAT_LINK_HERE"`
The user must replace the placeholder with the ChatGPT shared-conversation link. If the link is missing, private, expired, or unavailable, continue from the local reference files and this specification. Do not block the implementation on the chat URL.
Do not silently change the control logic because a different rule appears more realistic. Port the approved logic first. Any proposed scientific improvement must be isolated behind an optional feature flag and documented separately from the baseline.

## 3. Repository-first rule
Before coding:
1. Inspect the repository structure, package manager, frontend framework, backend framework, test runner, chart library, design system, authentication pattern, API conventions, and deployment method.
2. Reuse the repository’s current stack and conventions where they are suitable.
3. Do not create a parallel application when an integration point already exists.
4. Do not add a new production dependency without checking whether an equivalent dependency already exists.
5. Keep the numerical simulation core independent of UI components and framework state.
6. Keep all engineering constants and calibration values in one typed configuration module. Do not hide values inside UI components.
If the repository has no established implementation stack, use this default:
- TypeScript for the deterministic simulation core.
- React with TypeScript for the interface.
- A Web Worker for simulation so the interface remains responsive.
- The existing chart library; otherwise use a mature interactive chart library already compatible with the repository.
- SVG for the animated vehicle and power-flow diagram.
- A lightweight Node/TypeScript API only when the platform requires server execution or persistent result storage.
A Python backend is acceptable when the existing platform is Python-based. The API and numerical behaviour must remain the same regardless of language.

## 4. Required software architecture
Implement four clearly separated layers.

### 4.1 Deterministic simulation core
A pure, stateful numerical module with no DOM, chart, database, network, or framework dependency.
Required public capabilities:
- `createSimulation(config)`
- `reset(initialConditions?)`
- `step(input, dtSeconds)`
- `runScenario(request)`
- `getCurrentFrame()`
- `validateConfig(config)`
- `serializeState()` and `restoreState(state)` when useful to the existing platform
The same initial state, parameters, time step, and scenario must always produce the same result.

### 4.2 Platform adapter
Map platform values to the simulation input contract and map simulation frames to the platform output contract. This is the only layer that may know the repository’s API, state-management, database, worker, or event-stream conventions.

### 4.3 User interface
Provide validated controls, live status, a data-driven vehicle/power-flow animation, charts with legends and units, run controls, result summaries, and export functions.

### 4.4 Tests and verification
Provide unit tests, state-machine tests, numerical golden tests, UI tests, and integration tests. The implementation is not complete until the baseline port passes the acceptance tests in this file.

## 5. Units, sign convention, and numerical policy
Use SI units internally unless a field below explicitly uses another unit.
- Time: seconds.
- Speed internally: metres per second.
- Display speed: kilometres per hour.
- Power: kilowatts.
- Energy: kilowatt-hours.
- Force: newtons.
- Mass: kilograms.
- Fuel rate: grams per second.
- Fuel used: litres using `740 g/L`.
- SOC: fraction internally and percentage in the interface.
Sign convention:
- Positive requested and delivered wheel power means propulsion.
- Negative wheel power means braking.
- Positive battery power means discharge from the battery.
- Negative battery power means charging.
- Positive MG1 DC power means electrical generation to the DC bus.
- Positive MG2 mechanical power means traction.
- Negative MG2 mechanical power means regeneration.
Do not reverse these signs in the UI or API. Labels may explain them, but values must remain consistent.
Numerical baseline:
- Default time step: `0.1 s`.
- Default duration: `30 s`.
- Clamp or reject invalid user inputs before simulation.
- Never allow `NaN`, `Infinity`, or division by zero into a returned frame.
- Preserve the approved saturation and clamp behaviour described below.

## 6. Typed data contract
Implement equivalent typed records or schemas in the repository’s language.

```text
UserInputs
  scenarioCode: integer                 default 1, valid 1..4
  initialSoc: number                    default 0.60, valid 0.30..0.80
  demandScale: number                   default 1.00, recommended 0.50..1.50
  roadGradePercent: number              default 0, recommended -10..+10
  manualWheelPowerKw: number            default 25, valid -80..+120
VehicleParameters
  massKg: number                        default 1500, minimum 500
  dragCoefficient: number               default 0.29, minimum 0.10
  frontalAreaM2: number                 default 2.20, minimum 1.00
  rollingResistanceCoefficient: number  default 0.012, minimum 0.005
  wheelRadiusM: number                  default 0.31, minimum 0.15
PowertrainParameters
  batteryCapacityKWh: number            default 2.0, minimum 0.5
  engineMaxKw: number                   default 75, minimum 20
  mg1MaxKw: number                      default 55, minimum 10
  mg2MaxKw: number                      default 60, minimum 10
  socLow: number                        default 0.45, clamped 0.32..0.65
  socHigh: number                       default 0.65, clamped to socLow+0.05..0.78
```

Default vectors from the Simulink model:

```text
USER INPUTS       [1, 0.60, 1.0, 0, 25]
VEHICLE PARAMETERS [1500, 0.29, 2.2, 0.012, 0.31]
POWERTRAIN PARAMETERS [2.0, 75, 55, 60, 0.45, 0.65]
```

Return one `SimulationFrame` for each time step:

```text
SimulationFrame
  timeSeconds
  targetSpeedKmh
  actualSpeedKmh
  requestedWheelPowerKw
  deliveredWheelPowerKw
  unmetPowerKw
  engineShaftPowerKw
  mg1DcPowerKw
  mg2MechanicalPowerKw
  batteryPowerKw
  modeCode
  modeLabel
  reasonCode
  reasonLabel
  transitionActive
  clutchCommand
  socFraction
  socPercent
  fuelRateGps
  fuelUsedLitres
  recoveredEnergyKWh
  pathEfficiencyFraction
  pathEfficiencyPercent
  mechanicalLossKw
  electricalLossKw
  overallEfficiencyFraction
  overallEfficiencyPercent
```

A completed run must also return summary values:
- Start and final SOC.
- Total fuel used.
- Total recovered energy.
- Distance travelled.
- Root-mean-square and maximum speed error.
- Time and percentage in each mode.
- Number and time of mode transitions.
- Total unmet-power energy.
- Mechanical and electrical loss energy.
- Average and energy-weighted path efficiency where meaningful.
- Input configuration, model version, time step, and duration.

## 7. Enumerations
Use readable enumerations internally and expose both readable labels and numeric codes.

### 7.1 Mode codes

```text
0 READY
1 ELECTRIC_ONLY
2 SERIES
3 MECHANICAL_DRIVE
4 COMBINED_DRIVE
5 ENGINE_CHARGING
6 REGENERATIVE
7 LIMITED
```

### 7.2 Reason codes

```text
0 NONE
1 LOW_DEMAND_SOC_OK
2 LOW_SPEED_OR_DIRECT_PATH_BLOCKED
3 MECHANICAL_REGION
4 HIGH_DEMAND
5 LOW_SOC_CHARGING
6 BRAKING_REQUEST
7 COMPONENT_LIMIT
8 VEHICLE_STOPPED
```

The UI must never display only an unexplained integer. Show the readable label, numeric code, and a short human explanation.

## 8. Persistent simulation state
The baseline state contains:

```text
vehicleSpeedMps
socFraction
fuelMassG
recoveredEnergyKWh
modeCode
modeDwellSeconds
transitionTimerSeconds
previousTimeSeconds
integralSpeedError
```

Reset behaviour:
- `vehicleSpeedMps = 0`
- `socFraction = clamp(initialSoc, 0.30, 0.80)`
- fuel and recovered energy are zero.
- mode is READY.
- timers and integral error are zero.
For each call, derive `dt = currentTime - previousTime`. If `dt <= 0` or `dt > 1.0`, use `0.1 s` to match the approved model.

## 9. Target-speed scenarios
Implement these profiles exactly for the baseline. Values are km/h.

### Scenario 1 — all-mode verification

```text
0 <= t < 3:    target = 8.333 * t
3 <= t < 6:    target = 25 + 8.333 * (t - 3)
6 <= t < 10:   target = 50 + 6.25 * (t - 6)
10 <= t < 13:  target = 75
13 <= t < 17:  target = 75 + 8.75 * (t - 13)
17 <= t < 20:  target = 110 - 10 * (t - 17)
20 <= t < 23:  target = max(0, 80 - 26.667 * (t - 20))
23 <= t < 29:  target = current actual speed in km/h; reset integral error to zero
29 <= t:       target = 0
```

Between `23` and `29 s`, Scenario 1 intentionally applies a low-SOC control stimulus described in Section 11. It is a verification scenario, not a fuel-economy cycle. Show this warning in the interface.

### Scenario 2 — urban stop-and-go

```text
0 <= t < 5:    target = 8 * t
5 <= t < 9:    target = 40
9 <= t < 13:   target = max(0, 40 - 10 * (t - 9))
13 <= t < 18:  target = 7 * (t - 13)
18 <= t < 23:  target = 35
23 <= t:       target = max(0, 35 - 5 * (t - 23))
```

### Scenario 3 — highway

```text
0 <= t < 8:    target = 12.5 * t
8 <= t < 24:   target = 100
24 <= t:       target = max(0, 100 - 16.667 * (t - 24))
```

### Scenario 4 — manual wheel power
Use a nominal target speed of `60 km/h`, but calculate requested wheel power directly from `manualWheelPowerKw * demandScale`.

## 10. Driver and longitudinal vehicle equations
Constants:

```text
rho = 1.225 kg/m3
 g = 9.81 m/s2
```

Road angle:

```text
gradeFraction = roadGradePercent / 100
theta = atan(gradeFraction)
```

Driver:

```text
speedError = targetSpeedKmh / 3.6 - vehicleSpeedMps
integralSpeedError = clamp(integralSpeedError + speedError * dt, -20, 20)
accelerationCommand = clamp(0.75 * speedError + 0.05 * integralSpeedError, -3.5, 2.6)
```

Road load:

```text
Faero = 0.5 * rho * Cd * Af * vehicleSpeedMps^2
Froll = massKg * g * Crr * cos(theta)
Fgrade = massKg * g * sin(theta)
Fresistance = Faero + Froll + Fgrade
```

Requested wheel power:

```text
if scenarioCode == 4:
  requestedWheelPowerKw = manualWheelPowerKw * demandScale
else:
  requestedWheelPowerKw =
    ((massKg * accelerationCommand + Fresistance) * max(vehicleSpeedMps, 1.0))
    / 1000 * demandScale
requestedWheelPowerKw = clamp(requestedWheelPowerKw, -80, 120)
```

Preserve the `max(vehicleSpeedMps, 1.0)` baseline behaviour. Do not substitute another launch model in the baseline port.

## 11. Supervisory state-machine selection
Calculate:

```text
speedKmh = vehicleSpeedMps * 3.6
mechanicalFeasible = speedKmh >= 52 and speedKmh <= 135
electricFeasible =
  socFraction > socLow + 0.015
  and requestedWheelPowerKw <= min(28, mg2MaxKw * 0.90)
  and speedKmh < 58
controlSoc = socFraction
if scenarioCode == 1 and 23 <= timeSeconds < 29:
  controlSoc = min(controlSoc, socLow - 0.015)
```

Apply this exact priority:

```text
if requestedWheelPowerKw < -1.0:
  candidate = REGENERATIVE
  reason = BRAKING_REQUEST
else if controlSoc < socLow and requestedWheelPowerKw < 16:
  candidate = ENGINE_CHARGING
  reason = LOW_SOC_CHARGING
else if abs(requestedWheelPowerKw) < 0.8 and vehicleSpeedMps < 0.4:
  candidate = READY
  reason = VEHICLE_STOPPED
else if requestedWheelPowerKw > 47 and mechanicalFeasible and socFraction > socLow:
  candidate = COMBINED_DRIVE
  reason = HIGH_DEMAND
else if mechanicalFeasible
     and requestedWheelPowerKw >= 8
     and requestedWheelPowerKw <= 47
     and controlSoc >= socLow:
  candidate = MECHANICAL_DRIVE
  reason = MECHANICAL_REGION
else if electricFeasible and requestedWheelPowerKw >= 0:
  candidate = ELECTRIC_ONLY
  reason = LOW_DEMAND_SOC_OK
else if requestedWheelPowerKw >= 0:
  candidate = SERIES
  reason = LOW_SPEED_OR_DIRECT_PATH_BLOCKED
else:
  candidate = LIMITED
  reason = COMPONENT_LIMIT
```

Transition behaviour:

```text
modeDwellSeconds += dt
transitionTimerSeconds = max(transitionTimerSeconds - dt, 0)
transitionActive = false
if candidate != currentMode:
  if candidate == REGENERATIVE or modeDwellSeconds >= 0.45:
    currentMode = candidate
    modeDwellSeconds = 0
    transitionTimerSeconds = 0.35
    transitionActive = true
  else:
    transitionActive = true
else if transitionTimerSeconds > 0:
  transitionActive = true
```

Braking therefore has immediate priority. Other mode changes wait for the minimum dwell time.

## 12. Power allocation and efficiencies
Use these baseline values:

```text
etaFinalDrive = 0.95
etaMechanicalPath = 0.92
etaGenerator = 0.90
etaInverter = 0.96
etaMotor = 0.91
etaBatteryDischarge = 0.95
etaBatteryCharge = 0.94
fuelLowerHeatingValueKjPerG = 44.0
auxiliaryPowerKw = 1.0
```

Initialize all powers and losses to zero at every step.

### READY

```text
deliveredWheelPowerKw = 0
reason = VEHICLE_STOPPED
```

### ELECTRIC_ONLY

```text
mg2MechanicalPowerKw = min(max(requestedWheelPowerKw / etaFinalDrive, 0), mg2MaxKw)
deliveredWheelPowerKw = mg2MechanicalPowerKw * etaFinalDrive
batteryPowerKw = mg2MechanicalPowerKw /
  (etaMotor * etaInverter * etaBatteryDischarge) + auxiliaryPowerKw
electricalLossKw = max(batteryPowerKw - deliveredWheelPowerKw, 0)
pathEfficiency = deliveredWheelPowerKw / max(batteryPowerKw, 0.1)
```

### SERIES

```text
mg2MechanicalPowerKw = min(max(requestedWheelPowerKw / etaFinalDrive, 0), mg2MaxKw)
deliveredWheelPowerKw = mg2MechanicalPowerKw * etaFinalDrive
dcRequiredKw = mg2MechanicalPowerKw / (etaMotor * etaInverter) + auxiliaryPowerKw
engineShaftPowerKw = min(
  engineMaxKw,
  min(mg1MaxKw / etaGenerator, dcRequiredKw / (etaGenerator * etaInverter) + 4)
)
mg1DcPowerKw = engineShaftPowerKw * etaGenerator * etaInverter
batteryPowerKw = (dcRequiredKw - mg1DcPowerKw) / etaBatteryDischarge
electricalLossKw = max(
  engineShaftPowerKw + max(batteryPowerKw, 0) - deliveredWheelPowerKw,
  0
)
pathEfficiency = deliveredWheelPowerKw /
  max(engineShaftPowerKw + max(batteryPowerKw, 0), 0.1)
```

### MECHANICAL_DRIVE

```text
clutchCommand = 1
engineShaftPowerKw = min(
  max(requestedWheelPowerKw / (etaMechanicalPath * etaFinalDrive), 0),
  engineMaxKw
)
mechanicalWheelPowerKw = engineShaftPowerKw * etaMechanicalPath * etaFinalDrive
deliveredWheelPowerKw = mechanicalWheelPowerKw
mechanicalLossKw = max(engineShaftPowerKw - deliveredWheelPowerKw, 0)
pathEfficiency = deliveredWheelPowerKw / max(engineShaftPowerKw, 0.1)
```

### COMBINED_DRIVE

```text
clutchCommand = 1
engineShaftPowerKw = min(
  max(0.70 * requestedWheelPowerKw / (etaMechanicalPath * etaFinalDrive), 15),
  engineMaxKw
)
mechanicalWheelPowerKw = engineShaftPowerKw * etaMechanicalPath * etaFinalDrive
remainingWheelPowerKw = max(requestedWheelPowerKw - mechanicalWheelPowerKw, 0)
mg2MechanicalPowerKw = min(remainingWheelPowerKw / etaFinalDrive, mg2MaxKw)
electricalWheelPowerKw = mg2MechanicalPowerKw * etaFinalDrive
deliveredWheelPowerKw = mechanicalWheelPowerKw + electricalWheelPowerKw
batteryPowerKw = mg2MechanicalPowerKw /
  (etaMotor * etaInverter * etaBatteryDischarge) + auxiliaryPowerKw
mechanicalLossKw = max(engineShaftPowerKw - mechanicalWheelPowerKw, 0)
electricalLossKw = max(batteryPowerKw - electricalWheelPowerKw, 0)
pathEfficiency = deliveredWheelPowerKw /
  max(engineShaftPowerKw + batteryPowerKw, 0.1)
```

### ENGINE_CHARGING

```text
engineShaftPowerKw = min(engineMaxKw, min(mg1MaxKw / etaGenerator, 30))
mg1DcPowerKw = engineShaftPowerKw * etaGenerator * etaInverter
mg2MechanicalPowerKw = min(
  max(requestedWheelPowerKw / etaFinalDrive, 0),
  min(mg2MaxKw, 12)
)
deliveredWheelPowerKw = mg2MechanicalPowerKw * etaFinalDrive
tractionDcPowerKw = mg2MechanicalPowerKw / (etaMotor * etaInverter) + auxiliaryPowerKw
chargePowerKw = max(mg1DcPowerKw - tractionDcPowerKw, 0)
batteryPowerKw = -chargePowerKw * etaBatteryCharge
electricalLossKw = max(
  engineShaftPowerKw - deliveredWheelPowerKw - max(-batteryPowerKw, 0),
  0
)
pathEfficiency =
  (deliveredWheelPowerKw + max(-batteryPowerKw, 0)) /
  max(engineShaftPowerKw, 0.1)
```

### REGENERATIVE

```text
regenerativeWheelPowerKw = max(
  requestedWheelPowerKw,
  -min(55, mg2MaxKw)
)
deliveredWheelPowerKw = regenerativeWheelPowerKw
mg2MechanicalPowerKw = regenerativeWheelPowerKw / etaFinalDrive
storedDcPowerKw = (-mg2MechanicalPowerKw) * etaMotor * etaInverter * etaBatteryCharge
batteryPowerKw = -min(storedDcPowerKw, 35)
electricalLossKw = max((-deliveredWheelPowerKw) - (-batteryPowerKw), 0)
pathEfficiency = (-batteryPowerKw) / max(-deliveredWheelPowerKw, 0.1)
```

### LIMITED

```text
deliveredWheelPowerKw = clamp(requestedWheelPowerKw, -25, 20)
reason = COMPONENT_LIMIT
```

## 13. Engine fuel, battery SOC, energy, and vehicle motion
Engine fuel:

```text
if engineShaftPowerKw > 0.1:
  loadFraction = clamp(engineShaftPowerKw / engineMaxKw, 0, 1)
  engineEfficiency = 0.24 + 0.14 * (1 - abs(loadFraction - 0.65) / 0.65)
  engineEfficiency = clamp(engineEfficiency, 0.22, 0.38)
  fuelRateGps = engineShaftPowerKw /
    (engineEfficiency * fuelLowerHeatingValueKjPerG)
else:
  engineEfficiency = 0
  fuelRateGps = 0
fuelMassG += fuelRateGps * dt
fuelUsedLitres = fuelMassG / 740
```

Battery:

```text
socFraction = socFraction - batteryPowerKw * dt /
  (3600 * batteryCapacityKWh)
socFraction = clamp(socFraction, 0.30, 0.80)
if batteryPowerKw < 0:
  recoveredEnergyKWh += (-batteryPowerKw) * dt / 3600
```

Vehicle motion:

```text
if abs(vehicleSpeedMps) > 0.8:
  driveForceN = deliveredWheelPowerKw * 1000 / max(vehicleSpeedMps, 0.8)
else:
  driveForceN = deliveredWheelPowerKw * 1000 / 0.8
actualAcceleration = clamp(
  (driveForceN - Fresistance) / massKg,
  -5.0,
  3.0
)
vehicleSpeedMps = max(vehicleSpeedMps + actualAcceleration * dt, 0)
```

Unmet power:

```text
unmetPowerKw = max(requestedWheelPowerKw - deliveredWheelPowerKw, 0)
```

Overall instantaneous efficiency:

```text
if deliveredWheelPowerKw >= 0:
  usefulPowerKw = deliveredWheelPowerKw + max(-batteryPowerKw, 0)
  inputPowerKw = fuelRateGps * fuelLowerHeatingValueKjPerG + max(batteryPowerKw, 0)
else:
  usefulPowerKw = max(-batteryPowerKw, 0)
  inputPowerKw = max(-deliveredWheelPowerKw, 0)
overallEfficiency =
  clamp(usefulPowerKw / inputPowerKw, 0, 1.2) when inputPowerKw > 0.1
  otherwise 0
```

The `1.2` cap is part of the baseline model and must be preserved even though values above 100% require careful boundary interpretation.

## 14. Scope-equivalent chart groups
The interface must reproduce the six Simulink Scope groups. Every chart must show a visible legend, axis units, hover values, and export capability.
1. **Vehicle Speed**
   - Target Speed (km/h)
   - Actual Speed (km/h)
2. **Wheel Power**
   - Requested Wheel Power (kW)
   - Delivered Wheel Power (kW)
   - Unmet Power (kW)
3. **Component Power**
   - Engine Shaft (kW)
   - MG1 DC (kW)
   - MG2 Mechanical (kW)
   - Battery +discharge / -charge (kW)
   - Wheel Power (kW)
4. **Control State**
   - Mode Code
   - Reason Code
   - Transition Active
   - Clutch Command
5. **Battery and Fuel**
   - SOC (%)
   - Fuel Rate (g/s)
   - Fuel Used (L)
   - Recovered Energy (kWh)
6. **Efficiency and Loss**
   - Path Efficiency (%)
   - Mechanical Loss (kW)
   - Electrical Loss (kW)
   - Overall Energy Efficiency (%)
Also provide a mode timeline and a mode-distribution summary. Do not merge traces with incompatible units onto an unreadable single axis without a clear dual-axis or separated-panel design.

## 15. User-interface requirements
The interface must be understandable to a learner who has not opened the code.

### 15.1 Input panel
Provide:
- Scenario selector with plain-language descriptions.
- Initial SOC control.
- Demand-scale control.
- Road-gradient control.
- Manual wheel-power control shown only or emphasized for Scenario 4.
- Vehicle parameter section.
- Powertrain parameter section.
- Restore-defaults action.
- Inline range validation, unit labels, and helpful descriptions.

### 15.2 Run controls
Provide:
- Run.
- Pause and resume when supported by the platform.
- Stop.
- Reset.
- Single-step or scrub/playback control when practical.
- Playback speed controls such as 0.5x, 1x, 2x, and 4x.
- Progress indicator and simulation time.
Simulation speed must not alter numerical time step or results.

### 15.3 Live status
Show prominent cards for:
- Active mode label and code.
- Reason label and code.
- Target and actual speed.
- SOC.
- Engine on/off.
- Clutch open/locked.
- Requested, delivered, and unmet wheel power.
- Fuel used.
- Recovered energy.

### 15.4 Animated vehicle and power flow
A graphical visual is required because the research contribution is educational transparency.
Mandatory minimum:
- A responsive 2D SVG side-view vehicle or simplified drivetrain schematic.
- Wheel rotation rate driven by actual vehicle speed.
- Road inclination driven by road grade.
- Engine icon visibly active when engine shaft power is positive.
- Battery fill driven by SOC.
- Battery charge/discharge direction shown correctly.
- Direct clutch visibly open or locked.
- Animated directional arrows whose direction and relative intensity follow component powers.
- Brake lamps or a clear braking indication during regenerative mode.
- Current mode and reason shown beside the animation.
Required power-flow paths:
- Battery → inverter → MG2 → wheels for electric-only.
- Engine → MG1 → DC bus → MG2 → wheels for series.
- Engine → clutch/driveline → wheels for mechanical drive.
- Mechanical and electrical branches simultaneously for combined drive.
- Engine → MG1 → battery, with optional small traction branch, for engine charging.
- Wheels → MG2 → battery for regeneration.
The animation must be generated from live model data. Do not use a static generated picture as a substitute.
A full 3D car is optional, not required. Use 3D only when the existing platform already contains a suitable 3D framework and it will not delay the verified simulation. A clean 2D SVG power-flow animation is the preferred baseline.

### 15.5 Results view
After each run, show:
- Summary cards.
- All six chart groups.
- Mode timeline and mode distribution.
- Transition event table with time, previous mode, new mode, and reason.
- Parameter snapshot.
- Warnings, including Scenario 1’s artificial low-SOC stimulus.
- Scientific interpretation prompts, not unsupported automatic conclusions.

### 15.6 Export
Provide:
- CSV time-series export.
- JSON run export including metadata and parameters.
- Chart image export if supported by the current chart library.
- A printable result summary or PDF only when the platform already supports it without heavy additional dependencies.

## 16. Platform integration contract
Adapt to the repository’s established API style, but preserve an equivalent contract.
Suggested operations:

```text
GET  /hybrid-model/schema
GET  /hybrid-model/scenarios
POST /hybrid-model/validate
POST /hybrid-model/run
POST /hybrid-model/reset
GET  /hybrid-model/runs/:id
GET  /hybrid-model/runs/:id/export?format=json|csv
```

For live simulation, use the platform’s existing event mechanism. If none exists, use a Web Worker for browser-local execution or a WebSocket/server-sent event stream for server execution.
Do not send one network request for every 0.1-second step unless the platform architecture explicitly requires it. Batch or stream efficiently.
Version the model contract, for example:

```text
modelId: "sphev-supervisory-control"
modelVersion: "1.0.0-baseline"
contractVersion: "1.0"
```

## 17. Validation and golden-reference tests

### 17.1 Formula checks
With default vehicle values on level ground at zero speed:

```text
rollingResistanceForce ≈ 176.58 N
```

At a +5% grade with default mass:

```text
gradeForce ≈ 734.83 N
```

For a 20 kW electric-only wheel request before other limits:

```text
MG2 mechanical power ≈ 21.0526 kW
Battery power ≈ 26.3671 kW
Electrical loss ≈ 6.3671 kW
Path efficiency ≈ 75.8522%
```

Use practical floating-point tolerances.

### 17.2 Scenario 1 golden sequence
Using all default parameters and `dt = 0.1 s`, the baseline software port should produce this approximate confirmed-mode sequence:

```text
0.0 s   READY
0.4 s   ELECTRIC_ONLY
4.4 s   SERIES
7.4 s   COMBINED_DRIVE
10.5 s  MECHANICAL_DRIVE
13.8 s  COMBINED_DRIVE
17.5 s  MECHANICAL_DRIVE
18.0 s  REGENERATIVE
23.0 s  ENGINE_CHARGING
29.0 s  REGENERATIVE
```

Allow a transition-time tolerance of approximately one or two time steps only. A larger difference requires investigation and documentation.
Approximate values at `30.0 s` for the exact baseline port:

```text
actualSpeedKmh ≈ 69.60
socFraction ≈ 0.60279
fuelUsedLitres ≈ 0.07706
recoveredEnergyKWh ≈ 0.08269
modeCode = 6
reasonCode = 6
```

Use reasonable numerical tolerances, but do not weaken tests simply to pass an incorrect port.

### 17.3 Behaviour tests
Test at least:
- Braking immediately overrides propulsion modes.
- Low SOC and low positive demand select engine charging.
- High demand in the mechanical speed region selects combined drive.
- Moderate demand in the mechanical speed region selects mechanical drive.
- Low demand with sufficient SOC selects electric-only.
- Positive demand outside direct-drive feasibility selects series.
- Mode dwell and transition timer behave as specified.
- Clutch command is `1` only in mechanical and combined modes.
- Negative battery power increases SOC.
- Positive battery power decreases SOC.
- Reduced MG2 rating can create unmet power.
- Invalid inputs return clear validation errors or safe clamps.
- Repeated identical runs return identical results.
- No output contains `NaN` or `Infinity`.

### 17.4 UI and accessibility tests
Verify:
- Every chart legend is visible.
- Units are visible.
- Keyboard access works for controls.
- Form controls have labels.
- Information is not communicated by colour alone.
- Desktop and mobile layouts are readable.
- Animation can be reduced or disabled when the user prefers reduced motion.
- Reset restores defaults and clears prior state.

## 18. Visual proof required from Codex
Do not finish with code only. Produce visual evidence that the integrated module works.
Required visual deliverables in the repository documentation or task response:
1. One desktop dashboard screenshot during a combined-drive or mechanical-drive event.
2. One screenshot during regenerative braking showing reverse energy flow to the battery.
3. One results-screen screenshot showing charts with visible legends.
4. One narrow/mobile screenshot proving responsive layout.
5. A short animated GIF, MP4, or equivalent browser preview showing the vehicle/power-flow animation through at least three modes. If the execution environment cannot record animation, provide a reproducible command and the working interactive preview route, plus the four screenshots above.
Use real simulation output for these visuals. Do not fabricate values manually.

## 19. Documentation required
Create or update:
- A module README explaining setup, architecture, equations, sign conventions, scenarios, inputs, outputs, and limitations.
- API or adapter documentation.
- A parameter table with defaults, units, and ranges.
- An enumeration table.
- A test report listing commands run and results.
- A brief comparison showing that the software port matches the baseline golden outputs.
- Clear instructions for adding the module to the existing virtual-platform navigation.

## 20. Non-negotiable quality rules
- Do not embed the simulation equations inside React components or presentation widgets.
- Do not use random values in the baseline simulation.
- Do not claim experimental validation.
- Do not claim global optimality.
- Do not remove the mode and reason codes.
- Do not hide saturation or unmet power.
- Do not omit chart legends.
- Do not use a static car image as the only power-flow visual.
- Do not make Scenario 1 look like a regulatory or fuel-economy test.
- Do not alter sign conventions.
- Do not duplicate repository-wide authentication, routing, design-system, or persistence code.
- Do not expose arbitrary code execution or accept unvalidated executable expressions from users.
- Keep the baseline port small enough to audit and test.

## 21. Definition of done
The task is done only when all of the following are true:
- The simulation core reproduces the baseline formulas and state logic.
- Golden numerical and mode-sequence tests pass.
- The module is integrated into the existing platform, not left as an isolated demo.
- Users can edit parameters, run, pause/reset, and view results.
- The animated vehicle/power-flow visual responds to real outputs.
- All six chart groups have visible legends and units.
- Mode and reason codes are translated to readable explanations.
- Results can be exported to CSV and JSON.
- Responsive and accessibility checks pass.
- Documentation and visual proof are included.
- Build, lint, type-check, and test commands pass using the repository’s normal workflow.
- Codex reports every changed file, every command run, any remaining limitation, and the exact route or command for opening the finished interface.
