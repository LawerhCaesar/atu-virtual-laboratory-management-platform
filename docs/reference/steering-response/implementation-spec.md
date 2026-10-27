# Codex Implementation Instructions: Vehicle Steering Response Virtual-Platform Module

## Reference fields to complete before Codex starts

- **Shared ChatGPT conversation:** `PASTE_SHARED_CHATGPT_CONVERSATION_URL_HERE`
- **Reference Simulink model:** `Vehicle_Steering_Response_Organized_All_in_One_With_Legends.slx`
- **Human-readable implementation guide:** `Vehicle_Steering_Response_Virtual_Platform_Programmer_Guide.docx`

The shared-chat link is supplementary. This file is self-contained and is the authoritative implementation specification. Do not block implementation if the chat link is absent or inaccessible.

---

## 1. Mission

Convert the working Simulink concept into production-quality program code and integrate it into the existing virtual automotive platform as a clear, user-friendly **Vehicle Steering Response** module.

The completed module must let a user:

1. enter or adjust vehicle and steering parameters;
2. run a steering-response simulation without editing source code;
3. view the numerical response and time histories with correct legends and units;
4. replay a top-down animated vehicle following the calculated X-Y trajectory;
5. export the results in CSV and JSON form; and
6. pass the same eleven output signals to other virtual-platform modules through a stable software interface.

Do not use MATLAB or Simulink as a production runtime dependency. The equations below must be implemented directly in the platform's programming language.

---

## 2. Required working method for Codex

1. Inspect the repository before changing anything. Identify the existing frontend framework, backend framework, routing, component conventions, plotting library, testing framework, styling system, and API patterns.
2. Use the platform's existing language and framework wherever possible. Do not introduce a second application stack unnecessarily.
3. Keep the physics engine separate from the user interface. The same engine must be callable from the page, an API endpoint, automated tests, and future coupled vehicle models.
4. Preserve the equations, units, sign conventions, protections, state ordering, and output ordering in this file.
5. Make small, reviewable changes and run the repository's existing tests and linting after each material stage.
6. If the repository has no established web stack, use **TypeScript + React** for the interface and a pure TypeScript simulation engine. Use the current chart library if present; otherwise use a dependable library such as Plotly.js, ECharts, or Chart.js. Use SVG or HTML Canvas for the vehicle animation.
7. Do not consider the task complete until the implemented page runs, the baseline case matches the reference values, all plots have legends and units, and the vehicle animation is visible and usable.

---

## 3. Scientific scope and boundaries

This module represents a simplified **planar lateral-yaw bicycle model** for steering-response demonstration and practical learning.

It includes:

- road-wheel steering input;
- constant longitudinal vehicle speed;
- vehicle sideslip response;
- yaw-rate response;
- linear front and rear tyre lateral forces;
- lateral acceleration;
- turning radius;
- heading angle; and
- X-Y trajectory.

It does **not** model:

- suspension travel;
- body roll or pitch;
- wheel hop;
- lateral load transfer;
- nonlinear tyre saturation;
- road roughness;
- steering-column, rack, or power-assist dynamics;
- braking or traction control;
- electronic stability control; or
- a production vehicle controller.

The interface must state these boundaries clearly. Do not animate body roll, suspension motion, or tyre saturation because the equations do not calculate them.

---

## 4. Model data contract

### 4.1 Editable vehicle parameters

| Field | Symbol | Unit | Default | Validation |
|---|---:|---:|---:|---|
| Vehicle speed | V | km/h | 60 | non-negative; internal minimum U = 0.5 m/s |
| Base vehicle mass | m0 | kg | 1500 | non-negative |
| Payload | mp | kg | 0 | non-negative |
| Yaw moment of inertia | Iz | kg·m² | 2500 | must be greater than 0 |
| CG to front axle | a | m | 1.2 | must be greater than 0 |
| CG to rear axle | b | m | 1.6 | must be greater than 0 |
| Front axle cornering stiffness | Cf | N/rad | 80000 | must be greater than 0 |
| Rear axle cornering stiffness | Cr | N/rad | 80000 | must be greater than 0 |
| Steering ratio | is | dimensionless | 16 | must be greater than 0 |

The internal total mass is:

`m = clamp(m0 + mp, 100, 50000)`

The internal longitudinal speed is:

`U = max(V / 3.6, 0.5)`

### 4.2 Steering scenario parameters

The default scenario must reproduce the Simulink Step block:

| Field | Unit | Default |
|---|---:|---:|
| Steering profile | - | step |
| Road-wheel steering amplitude | deg | 1.0 |
| Step application time | s | 1.0 |
| Simulation duration | s | 10.0 |
| Numerical time step | s | 0.01 |

The minimum required profile is **step steering**. The interface may additionally provide sine steering and a doublet/lane-change-style input, but these are input generators only and must not change the vehicle equations.

For the step profile:

`delta_deg(t) = 0`, when `t < stepTime`

`delta_deg(t) = steeringAmplitudeDeg`, when `t >= stepTime`

The road-wheel angle used by the equations is:

`delta = delta_deg × pi / 180`

The steering-wheel angle output is:

`steeringWheelAngleDeg = delta_deg × steeringRatio`

---

## 5. State variables and initial conditions

Use this state order throughout the engine:

1. `beta` — vehicle sideslip angle, rad
2. `r` — yaw rate, rad/s
3. `psi` — heading angle, rad
4. `x` — global X position, m
5. `y` — global Y position, m

Initial state at `t = 0`:

`beta = 0, r = 0, psi = 0, x = 0, y = 0`

---

## 6. Governing equations

### 6.1 Front tyre slip angle

`alpha_f = delta - beta - (a × r / U)`

### 6.2 Rear tyre slip angle

`alpha_r = -beta + (b × r / U)`

### 6.3 Linear lateral tyre forces

`F_yf = C_f × alpha_f`

`F_yr = C_r × alpha_r`

### 6.4 Vehicle sideslip-rate equation

`beta_dot = (F_yf + F_yr) / (m × U) - r`

### 6.5 Yaw-rate equation

`r_dot = (a × F_yf - b × F_yr) / I_z`

### 6.6 Heading and trajectory equations

`psi_dot = r`

`pathAngle = psi + beta`

`x_dot = U × cos(pathAngle)`

`y_dot = U × sin(pathAngle)`

### 6.7 Derived outputs

`yawRateDegPerS = r × 180 / pi`

`sideslipDeg = beta × 180 / pi`

`lateralAccelerationMps2 = (F_yf + F_yr) / m`

`lateralAccelerationG = lateralAccelerationMps2 / 9.81`

`turningRadiusM = U / (abs(r) + 0.001)`

`headingDeg = psi × 180 / pi`

The `0.001` term in the turning-radius denominator is part of the reference model and must be retained.

---

## 7. Numerical solution requirement

Use a deterministic fixed-step fourth-order Runge-Kutta solver (RK4) with a default `dt = 0.01 s`. This gives repeatable results in a browser and is sufficiently accurate for this model.

At each step:

1. evaluate the steering input at the RK4 evaluation time;
2. calculate `alpha_f`, `alpha_r`, `F_yf`, and `F_yr`;
3. calculate the five state derivatives;
4. perform the RK4 update;
5. calculate the eleven reported outputs from the updated state; and
6. append one timestamped sample to the results array.

Allow `dt` to be changed only within a safe range, recommended `0.001 <= dt <= 0.05 s`. Reject invalid or non-finite inputs with a clear user message.

---

## 8. Reference TypeScript engine

Use this as the behavioural reference. Adapt naming and module structure to the repository, but do not alter the equations.

```ts
export type SteeringProfile = "step" | "sine" | "doublet";

export interface VehicleParameters {
  speedKmh: number;
  baseMassKg: number;
  payloadKg: number;
  yawInertiaKgM2: number;
  cgToFrontM: number;
  cgToRearM: number;
  frontCorneringStiffnessNPerRad: number;
  rearCorneringStiffnessNPerRad: number;
  steeringRatio: number;
}

export interface ScenarioParameters {
  profile: SteeringProfile;
  steeringAmplitudeDeg: number;
  stepTimeS: number;
  durationS: number;
  timeStepS: number;
  sineFrequencyHz?: number;
  doubletHalfDurationS?: number;
}

export interface ModelState {
  betaRad: number;
  yawRateRadPerS: number;
  headingRad: number;
  xM: number;
  yM: number;
}

export interface SimulationSample {
  timeS: number;
  roadWheelAngleDeg: number;
  steeringWheelAngleDeg: number;
  yawRateDegPerS: number;
  sideslipDeg: number;
  lateralAccelerationMps2: number;
  lateralAccelerationG: number;
  turningRadiusM: number;
  headingDeg: number;
  xM: number;
  yM: number;
  frontLateralForceN: number;
  rearLateralForceN: number;
}

export interface SimulationResult {
  parameters: VehicleParameters;
  scenario: ScenarioParameters;
  outputVectorOrder: string[];
  samples: SimulationSample[];
  final: SimulationSample;
}

interface InternalParameters {
  U: number;
  m: number;
  Iz: number;
  a: number;
  b: number;
  Cf: number;
  Cr: number;
  steeringRatio: number;
}

interface DerivativeResult {
  derivative: ModelState;
  roadWheelAngleDeg: number;
  frontLateralForceN: number;
  rearLateralForceN: number;
}

const DEG_TO_RAD = Math.PI / 180;
const RAD_TO_DEG = 180 / Math.PI;

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function requireFinitePositive(name: string, value: number): void {
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`${name} must be a finite number greater than zero.`);
  }
}

function validateInputs(
  vehicle: VehicleParameters,
  scenario: ScenarioParameters,
): void {
  const finiteFields: Array<[string, number]> = [
    ["speedKmh", vehicle.speedKmh],
    ["baseMassKg", vehicle.baseMassKg],
    ["payloadKg", vehicle.payloadKg],
    ["steeringAmplitudeDeg", scenario.steeringAmplitudeDeg],
    ["stepTimeS", scenario.stepTimeS],
    ["durationS", scenario.durationS],
    ["timeStepS", scenario.timeStepS],
  ];

  for (const [name, value] of finiteFields) {
    if (!Number.isFinite(value)) {
      throw new Error(`${name} must be finite.`);
    }
  }

  if (vehicle.speedKmh < 0 || vehicle.baseMassKg < 0 || vehicle.payloadKg < 0) {
    throw new Error("Speed, base mass, and payload cannot be negative.");
  }

  requireFinitePositive("yawInertiaKgM2", vehicle.yawInertiaKgM2);
  requireFinitePositive("cgToFrontM", vehicle.cgToFrontM);
  requireFinitePositive("cgToRearM", vehicle.cgToRearM);
  requireFinitePositive(
    "frontCorneringStiffnessNPerRad",
    vehicle.frontCorneringStiffnessNPerRad,
  );
  requireFinitePositive(
    "rearCorneringStiffnessNPerRad",
    vehicle.rearCorneringStiffnessNPerRad,
  );
  requireFinitePositive("steeringRatio", vehicle.steeringRatio);

  if (scenario.durationS <= 0) {
    throw new Error("durationS must be greater than zero.");
  }
  if (scenario.timeStepS < 0.001 || scenario.timeStepS > 0.05) {
    throw new Error("timeStepS must be between 0.001 and 0.05 seconds.");
  }
  if (scenario.stepTimeS < 0 || scenario.stepTimeS > scenario.durationS) {
    throw new Error("stepTimeS must lie within the simulation duration.");
  }
}

function steeringAtTime(t: number, scenario: ScenarioParameters): number {
  const amplitude = scenario.steeringAmplitudeDeg;

  switch (scenario.profile) {
    case "step":
      return t < scenario.stepTimeS ? 0 : amplitude;

    case "sine": {
      if (t < scenario.stepTimeS) return 0;
      const frequency = scenario.sineFrequencyHz ?? 0.25;
      return amplitude * Math.sin(2 * Math.PI * frequency * (t - scenario.stepTimeS));
    }

    case "doublet": {
      if (t < scenario.stepTimeS) return 0;
      const halfDuration = scenario.doubletHalfDurationS ?? 1.0;
      if (t < scenario.stepTimeS + halfDuration) return amplitude;
      if (t < scenario.stepTimeS + 2 * halfDuration) return -amplitude;
      return 0;
    }

    default:
      return 0;
  }
}

function internalParameters(vehicle: VehicleParameters): InternalParameters {
  return {
    U: Math.max(vehicle.speedKmh / 3.6, 0.5),
    m: clamp(vehicle.baseMassKg + vehicle.payloadKg, 100, 50000),
    Iz: vehicle.yawInertiaKgM2,
    a: vehicle.cgToFrontM,
    b: vehicle.cgToRearM,
    Cf: vehicle.frontCorneringStiffnessNPerRad,
    Cr: vehicle.rearCorneringStiffnessNPerRad,
    steeringRatio: vehicle.steeringRatio,
  };
}

function derivatives(
  timeS: number,
  state: ModelState,
  p: InternalParameters,
  scenario: ScenarioParameters,
): DerivativeResult {
  const roadWheelAngleDeg = steeringAtTime(timeS, scenario);
  const delta = roadWheelAngleDeg * DEG_TO_RAD;

  const alphaF = delta - state.betaRad - (p.a * state.yawRateRadPerS) / p.U;
  const alphaR = -state.betaRad + (p.b * state.yawRateRadPerS) / p.U;

  const Fyf = p.Cf * alphaF;
  const Fyr = p.Cr * alphaR;

  const betaDot = (Fyf + Fyr) / (p.m * p.U) - state.yawRateRadPerS;
  const yawRateDot = (p.a * Fyf - p.b * Fyr) / p.Iz;
  const headingDot = state.yawRateRadPerS;
  const pathAngle = state.headingRad + state.betaRad;
  const xDot = p.U * Math.cos(pathAngle);
  const yDot = p.U * Math.sin(pathAngle);

  return {
    derivative: {
      betaRad: betaDot,
      yawRateRadPerS: yawRateDot,
      headingRad: headingDot,
      xM: xDot,
      yM: yDot,
    },
    roadWheelAngleDeg,
    frontLateralForceN: Fyf,
    rearLateralForceN: Fyr,
  };
}

function addScaled(
  state: ModelState,
  derivative: ModelState,
  scale: number,
): ModelState {
  return {
    betaRad: state.betaRad + derivative.betaRad * scale,
    yawRateRadPerS:
      state.yawRateRadPerS + derivative.yawRateRadPerS * scale,
    headingRad: state.headingRad + derivative.headingRad * scale,
    xM: state.xM + derivative.xM * scale,
    yM: state.yM + derivative.yM * scale,
  };
}

function rk4Step(
  t: number,
  state: ModelState,
  dt: number,
  p: InternalParameters,
  scenario: ScenarioParameters,
): ModelState {
  const k1 = derivatives(t, state, p, scenario).derivative;
  const k2 = derivatives(
    t + dt / 2,
    addScaled(state, k1, dt / 2),
    p,
    scenario,
  ).derivative;
  const k3 = derivatives(
    t + dt / 2,
    addScaled(state, k2, dt / 2),
    p,
    scenario,
  ).derivative;
  const k4 = derivatives(
    t + dt,
    addScaled(state, k3, dt),
    p,
    scenario,
  ).derivative;

  return {
    betaRad:
      state.betaRad +
      (dt / 6) * (k1.betaRad + 2 * k2.betaRad + 2 * k3.betaRad + k4.betaRad),
    yawRateRadPerS:
      state.yawRateRadPerS +
      (dt / 6) *
        (k1.yawRateRadPerS +
          2 * k2.yawRateRadPerS +
          2 * k3.yawRateRadPerS +
          k4.yawRateRadPerS),
    headingRad:
      state.headingRad +
      (dt / 6) *
        (k1.headingRad + 2 * k2.headingRad + 2 * k3.headingRad + k4.headingRad),
    xM: state.xM + (dt / 6) * (k1.xM + 2 * k2.xM + 2 * k3.xM + k4.xM),
    yM: state.yM + (dt / 6) * (k1.yM + 2 * k2.yM + 2 * k3.yM + k4.yM),
  };
}

function sampleFromState(
  timeS: number,
  state: ModelState,
  p: InternalParameters,
  scenario: ScenarioParameters,
): SimulationSample {
  const response = derivatives(timeS, state, p, scenario);
  const totalLateralForce =
    response.frontLateralForceN + response.rearLateralForceN;
  const ay = totalLateralForce / p.m;

  return {
    timeS,
    roadWheelAngleDeg: response.roadWheelAngleDeg,
    steeringWheelAngleDeg: response.roadWheelAngleDeg * p.steeringRatio,
    yawRateDegPerS: state.yawRateRadPerS * RAD_TO_DEG,
    sideslipDeg: state.betaRad * RAD_TO_DEG,
    lateralAccelerationMps2: ay,
    lateralAccelerationG: ay / 9.81,
    turningRadiusM: p.U / (Math.abs(state.yawRateRadPerS) + 0.001),
    headingDeg: state.headingRad * RAD_TO_DEG,
    xM: state.xM,
    yM: state.yM,
    frontLateralForceN: response.frontLateralForceN,
    rearLateralForceN: response.rearLateralForceN,
  };
}

export function simulateSteeringResponse(
  vehicle: VehicleParameters,
  scenario: ScenarioParameters,
): SimulationResult {
  validateInputs(vehicle, scenario);
  const p = internalParameters(vehicle);
  const samples: SimulationSample[] = [];

  let state: ModelState = {
    betaRad: 0,
    yawRateRadPerS: 0,
    headingRad: 0,
    xM: 0,
    yM: 0,
  };

  let timeS = 0;
  samples.push(sampleFromState(timeS, state, p, scenario));

  while (timeS < scenario.durationS - 1e-12) {
    const dt = Math.min(scenario.timeStepS, scenario.durationS - timeS);
    state = rk4Step(timeS, state, dt, p, scenario);
    timeS += dt;
    samples.push(sampleFromState(timeS, state, p, scenario));
  }

  return {
    parameters: vehicle,
    scenario,
    outputVectorOrder: [
      "yawRateDegPerS",
      "sideslipDeg",
      "lateralAccelerationMps2",
      "lateralAccelerationG",
      "turningRadiusM",
      "headingDeg",
      "xM",
      "yM",
      "frontLateralForceN",
      "rearLateralForceN",
      "steeringWheelAngleDeg",
    ],
    samples,
    final: samples[samples.length - 1],
  };
}
```

---

## 9. Platform-facing output interface

Preserve this eleven-signal order exactly for coupling to the wider virtual platform:

| Index | Field | Unit |
|---:|---|---|
| 1 | `yawRateDegPerS` | deg/s |
| 2 | `sideslipDeg` | deg |
| 3 | `lateralAccelerationMps2` | m/s² |
| 4 | `lateralAccelerationG` | g |
| 5 | `turningRadiusM` | m |
| 6 | `headingDeg` | deg |
| 7 | `xM` | m |
| 8 | `yM` | m |
| 9 | `frontLateralForceN` | N |
| 10 | `rearLateralForceN` | N |
| 11 | `steeringWheelAngleDeg` | deg |

Expose both:

- a named object for readable application code; and
- an ordered numeric array for compatibility with an existing platform signal bus.

Example ordered vector:

```ts
const platformVector = [
  sample.yawRateDegPerS,
  sample.sideslipDeg,
  sample.lateralAccelerationMps2,
  sample.lateralAccelerationG,
  sample.turningRadiusM,
  sample.headingDeg,
  sample.xM,
  sample.yM,
  sample.frontLateralForceN,
  sample.rearLateralForceN,
  sample.steeringWheelAngleDeg,
];
```

If the platform uses a backend API, provide an endpoint equivalent to:

`POST /api/vehicle-dynamics/steering-response/simulate`

Suggested request:

```json
{
  "vehicle": {
    "speedKmh": 60,
    "baseMassKg": 1500,
    "payloadKg": 0,
    "yawInertiaKgM2": 2500,
    "cgToFrontM": 1.2,
    "cgToRearM": 1.6,
    "frontCorneringStiffnessNPerRad": 80000,
    "rearCorneringStiffnessNPerRad": 80000,
    "steeringRatio": 16
  },
  "scenario": {
    "profile": "step",
    "steeringAmplitudeDeg": 1,
    "stepTimeS": 1,
    "durationS": 10,
    "timeStepS": 0.01
  }
}
```

The response must contain parameters, scenario metadata, timestamped samples, the final sample, and the ordered output-vector definition.

---

## 10. User-interface requirements

Create a dedicated page or module titled:

**Vehicle Steering Response Modelling for Virtual-Platform Application**

### 10.1 Input panel

Group inputs clearly:

- **Steering scenario:** profile, road-wheel angle, application time, duration, time step.
- **Vehicle operating condition:** speed, base mass, payload.
- **Vehicle geometry and dynamics:** yaw inertia, `a`, `b`, `Cf`, `Cr`, steering ratio.

Each field must display its unit, default value, valid range or rule, and a short tooltip. Provide:

- Run Simulation;
- Pause/Play Animation;
- Reset to Defaults;
- Clear Results;
- Export CSV;
- Export JSON; and
- optional Save/Load Scenario controls if these patterns already exist in the platform.

### 10.2 Summary cards

Show the current or final values for:

- yaw rate;
- sideslip angle;
- lateral acceleration in m/s² and g;
- turning radius;
- heading angle;
- front and rear lateral tyre forces;
- steering-wheel angle; and
- final X and Y position.

### 10.3 Required plots and legends

Reproduce the four logical scope groups from the Simulink model. Every plot must show a title, axis labels, units, grid, and visible legend.

1. **Handling Response**
   - Yaw rate (deg/s)
   - Sideslip angle (deg)
   - Lateral acceleration (m/s²)

2. **Steering, Radius and Lateral Acceleration**
   - Steering-wheel angle (deg)
   - Turning radius (m)
   - Lateral acceleration (g)

3. **Trajectory and Heading**
   - X position (m)
   - Y position (m)
   - Heading angle (deg)

4. **Tyre Lateral Forces**
   - Front lateral force (N)
   - Rear lateral force (N)

Because variables in a group can have very different scales, use separate aligned panels, selectable traces, or multiple y-axes rather than compressing all lines into an unreadable plot.

---

## 11. Mandatory animated vehicle visual

A graphical vehicle output is required because the model calculates `x`, `y`, `psi`, and steering angle. Implement a lightweight **2D top-down vehicle animation** as the baseline visualisation.

The animation must show:

- a recognisable vehicle body;
- vehicle position from `xM` and `yM`;
- vehicle heading from `headingDeg`;
- front-wheel steering direction from `roadWheelAngleDeg`;
- a trajectory trail;
- current simulation time;
- current speed, yaw rate, sideslip, and lateral acceleration;
- play, pause, restart, speed-control, and time-scrubber controls;
- automatic view scaling or a follow-camera option; and
- a static final trajectory view after the animation ends.

Use SVG or Canvas unless the platform already has a 3D engine. A 3D vehicle may be added as an optional enhancement, but it is not required and must not delay delivery. Do not show suspension movement or body roll.

The final visual design should make the steering event obvious: before the steering step the vehicle travels straight; after the step it develops yaw, follows a curved path, and displays the corresponding response traces.

---

## 12. Assumptions and warning panel

Display a compact information panel stating:

- linear bicycle model;
- small-angle, linear-tyre assumption;
- constant longitudinal speed;
- zero initial states;
- planar lateral-yaw motion only;
- no roll, pitch, vertical suspension, braking, or tyre saturation; and
- educational/engineering simulation, not a road-safety or homologation tool.

Display warnings rather than silently accepting invalid parameters. The two reference protections that must remain are:

- speed internally limited to at least `0.5 m/s`; and
- total mass internally limited to `100–50000 kg`.

---

## 13. Reference validation case

Use this case to prove that the converted program reproduces the model:

- step road-wheel angle: `1 deg` at `t = 1 s`;
- vehicle speed: `60 km/h`;
- base mass: `1500 kg`;
- payload: `0 kg`;
- yaw inertia: `2500 kg·m²`;
- `a = 1.2 m`;
- `b = 1.6 m`;
- `Cf = 80000 N/rad`;
- `Cr = 80000 N/rad`;
- steering ratio: `16`;
- duration: `10 s`;
- RK4 time step: `0.01 s`.

Expected values at `t = 10 s`, allowing normal numerical tolerance:

| Output | Expected value |
|---|---:|
| Yaw rate | approximately `4.7027 deg/s` |
| Sideslip angle | approximately `-0.17837 deg` |
| Lateral acceleration | approximately `1.36797 m/s²` |
| Lateral acceleration | approximately `0.13945 g` |
| Turning radius | approximately `200.615 m` |
| Heading angle | approximately `41.876 deg` |
| X position | approximately `153.963 m` |
| Y position | approximately `51.465 m` |
| Front lateral force | approximately `1172.54 N` |
| Rear lateral force | approximately `879.41 N` |
| Steering-wheel angle | `16 deg` |

Acceptance tolerance for the converted engine: generally within `±1%` of these values. Position and heading may use `±2%` if the platform uses a different but documented high-quality numerical solver.

Also verify:

- zero steering produces essentially zero yaw rate, sideslip, lateral acceleration, lateral displacement, and tyre lateral forces;
- no result is NaN or infinite for valid inputs;
- increasing steering amplitude increases the response magnitude within the linear range;
- payload changes the transient response because total mass changes; and
- CSV/JSON exports contain the same samples displayed in the plots.

---

## 14. Software quality requirements

- Use typed interfaces or schemas for all parameters and outputs.
- Keep unit conversions in one clearly named location.
- Add unit tests for equations, RK4 integration, output ordering, validation, and the reference case.
- Add component/integration tests for parameter editing, running, reset, legends, export, and animation controls.
- Avoid duplicated equations in frontend and backend. One engine must be the source of truth.
- Do not use hidden magic numbers. Define gravity `9.81`, turning-radius epsilon `0.001`, minimum speed `0.5`, and mass bounds as named constants.
- Maintain responsive layout for desktop and tablet use.
- Use accessible labels, keyboard controls, sufficient contrast, and non-colour-only trace identification.
- Follow existing repository linting, formatting, documentation, and commit conventions.

---

## 15. Required final deliverables from Codex

Codex must deliver all of the following inside the platform repository:

1. reusable steering-response simulation engine;
2. platform adapter or API endpoint;
3. user-facing module/page integrated into navigation;
4. parameter-entry form with validation and units;
5. summary cards;
6. four correctly labelled plot groups with legends;
7. top-down animated vehicle and replay controls;
8. CSV and JSON export;
9. stable named output object and eleven-element output vector;
10. automated validation of the reference case;
11. concise developer documentation describing file locations, run commands, architecture, and extension points; and
12. visual evidence of completion: at least one screenshot of the full interface and one screenshot or short recording showing the animated car and trajectory.

The final Codex response must state:

- what was implemented;
- files added or changed;
- how to run it;
- how to access the page;
- validation results against the reference case;
- where the eleven-signal interface is exposed;
- where screenshots or recordings are stored; and
- any clearly bounded remaining limitation.

Do not return only a plan, mock-up, pseudocode, or isolated function. The required outcome is a working, integrated, visually complete virtual-platform module.
