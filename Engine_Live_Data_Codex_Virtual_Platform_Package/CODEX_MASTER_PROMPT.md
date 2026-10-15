# CODEX MASTER PROMPT — ENGINE LIVE-DATA DEMONSTRATION SECTION

**DO NOT BUILD A NEW PLATFORM. IMPLEMENT ONLY THE ENGINE LIVE-DATA DEMONSTRATION SECTION INSIDE THE COLLEAGUE'S ALREADY-EXISTING VIRTUAL AUTOMOTIVE PLATFORM/REPOSITORY.**

The colleague has already started the platform. This handover supplies the engineering models and behaviour for one section called **Engine Live-Data Demonstration**. Integrate that section into the existing product. Do not scaffold a replacement application, create a separate project or deployment, replace the platform shell, or redesign unrelated platform areas. References below to a page, laboratory, application or UI describe this engine section within its host platform.

## 0. Authority and engineering preservation

This master prompt is authoritative for implementation scope, integration workflow and the boundary between the virtual and physical stages. `CODEX_MASTER_PROMPT.txt` is an identical copy. If an older title, standalone prototype layout or copied source note suggests a new platform, follow this prompt.

Preserve all four engineering models and their input names, units, caps, defaults, equations, dependencies, branch priorities, timing, state codes, outputs, presets and expected test results. `engine_live_data_spec.json` is the machine-readable engineering specification; `reference/engineLiveDataModel.mjs` is the executable reference; `ACCEPTANCE_TESTS.md` and the reference tests define verification cases. Sections 5–7 below retain the detailed model contract. Adapt file placement, components and language to the repository without changing the mathematics or behaviour. Any engineering inconsistency must be reported with the relevant files and resolved before changing the affected model; do not silently recalibrate or simplify it.

The prototype is a standalone **reference demonstration only**, retained so the colleague can inspect behaviour. Its layout, styling and runtime are not an instruction to create a second platform or embed the whole prototype as a separate application. Source files in `source/` are preserved engineering reference material. Their historical wording does not authorise calibration changes in this integration task.

## 1. First inspect the existing repository

Before writing code:

1. Locate the actual existing platform repository and read its applicable instructions and documentation. Inspect the working tree and preserve the colleague's work. This handover folder is reference material, not the platform repository.
2. Identify the current framework, language, routing system, state-management approach, UI/component library, chart library, test runner and folder conventions. Inspect an existing comparable section and the files that register routes and navigation.
3. Reuse the platform's existing shell, layout, authentication, routing, navigation, typography, styles/design tokens, components, state conventions and chart library. Extend established patterns for the engine section rather than introducing a parallel architecture.
4. Identify the exact route or section registration, component locations, model location, state ownership and test commands before implementation. Briefly explain this integration map, then proceed with the authorised work.
5. Add only the Engine Live-Data Demonstration section and the minimal route/navigation wiring necessary to expose it. `/virtual-lab/engine-live-data` is only a suggested route; follow the repository's actual conventions. Keep the existing platform navigation and unrelated sections intact.
6. Do not create a new platform, scaffold a fresh app, add a separate deployment, replace the framework, or redesign unrelated areas. If the existing repository is missing or unavailable, request its location/access and stop dependent implementation instead of building a substitute. If a repository constraint blocks integration, describe the constraint and the specific information needed.
7. Keep the engine calculation code in a pure, testable module with no UI dependencies. Use the repository's language, dependencies, tests and build process. Add a dependency only when the required feature cannot reasonably use existing capabilities, and explain why.
8. Keep simulation state scoped to this feature using the host's conventions, and clean up simulation timers and subscriptions when leaving it. Verify navigation to and from existing sections and check that the feature introduces no unrelated regressions.

---

## 2. Project overview

### Research title

**Virtual Modelling and Physical Demonstration of Engine Live-Data Relationships for Virtual-Platform Integration**

### Purpose of the engine demonstration section

The section must help students understand that engine live data are interdependent. Students change only controlled input values. The section must:

1. cap each input within a stated reasonable range;
2. treat the capped value as the sensor or operating input received by the ECU;
3. calculate ECU-derived live-data values using the equations below;
4. generate related actuator commands and operating states;
5. display the full relationship clearly as:

**Student input → measured/status value → ECU-calculated value → commanded output → live result**

This section represents the **virtual stage only**. It does not connect to an ECU, CAN bus, OBD tool or physical engine. Fingerprint authorisation and voice/manual start are simulated operating inputs; recognition systems are outside this model.

### Separate physical stage

The separate physical study uses a Toyota 1NZ engine, a third-party programmable ECU, live-data software, fingerprint authorisation, offline voice control and other planned peripherals. The physical 1NZ setup has **no electric water pump**. ECT1/ECT2, the duty-controlled fan and the electric-water-pump command described in this package belong to the virtual cooling model; do not infer matching physical hardware from them. The virtual and physical stages are **tested independently, with no comparison between them**. Do not create comparison pages, combined datasets, agreement/error metrics or claims of numerical agreement. Keep virtual test evidence separate from physical-stage test evidence.

### Educational disclaimer

Display this notice in the laboratory:

> This is a simplified educational model. Its equations are not Toyota 1NZ, OEM or production ECU calibration data. Do not use it to control a road vehicle or safety-critical hardware.

---

## 3. Four required learning systems

Implement all four systems below as internal views of this single Engine Live-Data Demonstration section. They are not separate applications or replacements for existing platform sections.

### A. Fuel trim and injection control

Demonstrate the chain:

**Oxygen-sensor voltage → lambda estimate → STFT/equivalent closed-loop correction → injector pulse width**

Also show engine load, warm-up enrichment and battery-voltage compensation.

### B. Idle-speed and ignition control

Demonstrate the chain:

**Coolant temperature and actual RPM → target idle speed and RPM error → idle-control duty and ignition timing**

Also show the effect of accessory load, throttle position and manifold pressure.

### C. Dual-ECT cooling control

Demonstrate the chain:

**ECT1 and ECT2 voltages → calculated temperatures and sensor plausibility → PWM fan duty and virtual electric-water-pump duty**

The virtual cooling model includes virtual ECT1/ECT2, a duty-controlled fan and a virtual electric water pump. The electric water pump exists only in this virtual section; the physical 1NZ setup has none.

### D. Start/run and fuel-pump control

Demonstrate the state sequence:

**OFF → PRIME → CRANK → RUN → SHUTDOWN → OFF**

Use ignition status, fingerprint-authorisation status, voice/manual start request, stop request, emergency stop, engine speed and battery voltage. Display fuel-pump, starter, injection-enable and ignition-enable outputs.

---

## 4. Architecture requirements

Implement the feature in these layers:

### 4.1 Pure model core

Create a pure calculation module, for example:

- `engineLiveDataModel.ts`
- `engineLiveDataModel.js`
- or an equivalent file appropriate to the repository.

It must export:

- input definitions and ranges;
- default input values;
- engine-state codes and labels;
- `clamp`/input-sanitisation functions;
- ECT voltage-to-temperature conversion;
- start/run state-machine update;
- fuel calculations;
- idle/ignition calculations;
- cooling calculations;
- a single `stepEngineModel(inputs, internalState, dt)` function;
- types/interfaces when the project language supports them.

The core must not import UI components, browser globals or chart code.

### 4.2 Simulation controller

Use a fixed virtual calculation step of **0.05 s** to match the Simulink reference. The UI can be rendered less frequently, for example every 100–250 ms, while calculations continue at 0.05 s.

Maintain:

- current raw input values;
- capped/accepted input values;
- current engine-state code;
- elapsed time in the current state;
- current calculated outputs;
- rolling history for charts;
- run, pause and reset status.

### 4.3 User interface

Use the existing platform's components and styling. The page must remain understandable at normal laptop resolution and responsive on smaller screens.

### 4.4 Tests

Add unit tests for the pure model core and integration/component tests where the repository already supports them. Use the project's existing test runner. Adapt the tests in `reference/engineLiveDataModel.test.mjs` rather than introducing a second test framework unnecessarily.

---

## 5. Canonical student inputs

All student-adjustable values must be capped before calculations. Display the allowed range beside every control.

| Canonical signal | Display label | Unit/state | Minimum | Maximum | Default |
|---|---|---:|---:|---:|---:|
| `BatteryVoltage` | Battery voltage | V | 8.0 | 14.9 | 13.8 |
| `EngineSpeed` | Engine speed | rpm | 0 | 6500 | 800 |
| `ThrottlePosition` | Throttle position | % | 0 | 100 | 2 |
| `ManifoldPressure` | Manifold pressure | kPa | 20 | 105 | 35 |
| `O2SensorVoltage` | Oxygen-sensor voltage | V | 0.05 | 0.95 | 0.45 |
| `ECT1Voltage` | ECT1 sensor voltage | V | 0.2 | 4.8 | 1.0 |
| `ECT2Voltage` | ECT2 sensor voltage | V | 0.2 | 4.8 | 1.1 |
| `AccessoryLoad` | Accessory/electrical load | % | 0 | 100 | 10 |
| `IgnitionSwitch` | Ignition switch | 0/1 | 0 | 1 | 0 in the UI |
| `StartAuthorisation` | Fingerprint authorised | 0/1 | 0 | 1 | 0 in the UI |
| `StartRequest` | Voice/manual start request | 0/1 | 0 | 1 | 0 |
| `StopRequest` | Normal stop request | 0/1 | 0 | 1 | 0 |
| `EmergencyStop` | Emergency stop | 0/1 | 0 | 1 | 0 |
| `ACRequest` | Air-conditioning request | 0/1 | 0 | 1 | 0 |

The Simulink reference starts some status inputs at 1 for easy demonstration, but the application should open in a safe **OFF** state. Provide presets so a student can quickly load demonstration conditions.

### Input-control behaviour

- Numeric inputs: range slider plus numeric field when consistent with the existing UI library.
- Binary operating inputs: labelled switches.
- `StartRequest`: momentary button or short pulse, approximately 0.5 s.
- `StopRequest`: momentary button or short pulse.
- `EmergencyStop`: latching control that remains active until explicitly reset.
- If a user types a value outside the range, clamp it and clearly indicate the accepted value.
- Calculated values and output commands must never be directly editable by students.

---

## 6. Exact calculation logic

Use the following equations exactly unless a later approved specification explicitly changes them.

### 6.1 General clamp

```text
clip(value, minimum, maximum) = min(max(value, minimum), maximum)
```

### 6.2 ECT voltage-to-temperature conversion

First cap voltage to 0.2–4.8 V. Then use this educational piecewise relation:

```text
if V >= 4.3:
    T = -20 + (4.8 - V) × 40
else if V >= 3.5:
    T = 0 + (4.3 - V) × 31.25
else if V >= 2.5:
    T = 25 + (3.5 - V) × 25
else if V >= 1.5:
    T = 50 + (2.5 - V) × 25
else if V >= 1.0:
    T = 75 + (1.5 - V) × 30
else if V >= 0.6:
    T = 90 + (1.0 - V) × 37.5
else if V >= 0.3:
    T = 105 + (0.6 - V) × (20 / 0.3)
else:
    T = 125 + (0.3 - V) × 100

ECT temperature = clip(T, -20, 135) °C
```

### 6.3 Start/run state machine

State codes:

```text
0 = OFF
1 = PRIME
2 = CRANK
3 = RUN
4 = SHUTDOWN
```

Safe-start condition:

```text
IgnitionSwitch > 0.5
AND StartAuthorisation > 0.5
AND StartRequest > 0.5
AND EmergencyStop < 0.5
AND BatteryVoltage >= 9.5 V
```

Transitions:

```text
OFF:
    if safe-start condition is true → PRIME

PRIME:
    if EmergencyStop, StopRequest or IgnitionSwitch OFF → SHUTDOWN
    else after 2.0 s → CRANK

CRANK:
    if EmergencyStop, StopRequest, IgnitionSwitch OFF or BatteryVoltage < 8.5 V → SHUTDOWN
    else if EngineSpeed >= 500 rpm → RUN
    else after 5.0 s in CRANK → SHUTDOWN

RUN:
    if EmergencyStop, StopRequest or IgnitionSwitch OFF → SHUTDOWN

SHUTDOWN:
    after 0.5 s → OFF
```

State-derived outputs:

```text
FuelPumpState   = 1 in PRIME, CRANK or RUN; otherwise 0
StarterState    = 1 in CRANK only; otherwise 0
InjectionEnable = 1 in CRANK or RUN; otherwise 0
IgnitionEnable  = 1 in CRANK or RUN; otherwise 0
StartPermitted  = 1 in PRIME, CRANK or RUN; otherwise 0
```

### 6.4 Fuel trim and injection calculations

Cap local inputs again defensively.

```text
EngineLoad = clip(
    0.55 × ((MAP - 20) / 85) × 100
    + 0.45 × TPS,
    0,
    100
)

LambdaEstimate = clip(
    1.0 + (0.45 - O2Voltage) × 0.35,
    0.75,
    1.25
)

ClosedLoopActive = 1 only when:
    InjectionEnable = 1
    AND ECT1Temp >= 70 °C
    AND EngineSpeed >= 600 rpm

if ClosedLoopActive:
    STFT = clip((LambdaEstimate - 1.0) × 120, -25, 25) %
else:
    STFT = 0

WarmupEnrichment = clip((70 - ECT1Temp) × 0.5, 0, 40) %

BatteryCompensation = clip((13.8 - BatteryVoltage) × 0.18, 0, 1.20) ms

BaseInjectorPW = clip(
    1.0
    + 0.00035 × EngineSpeed
    + 0.025 × (MAP - 20)
    + 0.012 × TPS,
    1.0,
    15.0
) ms

if InjectionEnable:
    InjectorPW = clip(
        (BaseInjectorPW + BatteryCompensation)
        × (1 + (STFT + WarmupEnrichment) / 100),
        0,
        20
    ) ms
else:
    InjectorPW = 0
```

Use the label **“STFT / equivalent closed-loop fuel correction”** in explanatory text because a programmable ECU may use a different label.

### 6.5 Idle-speed and ignition calculations

```text
TargetIdleRPM = 750 + clip((80 - ECT1Temp) × 5.625, 0, 450)

IdleActive = 1 only when:
    EngineState = RUN
    AND TPS <= 5 %
    AND EngineSpeed < 2000 rpm

if IdleActive:
    RPMError = TargetIdleRPM - EngineSpeed
    IdleControlDuty = clip(
        25
        + 0.06 × RPMError
        + 0.25 × AccessoryLoad,
        0,
        100
    ) %
else:
    RPMError = 0
    IdleControlDuty = 0

if IgnitionEnable = 0:
    IgnitionTiming = 0° BTDC
else if EngineState = CRANK:
    IgnitionTiming = 5° BTDC
else:
    IgnitionTiming = clip(
        10
        + 0.004 × (EngineSpeed - 800)
        - 0.08 × (MAP - 35)
        + 0.015 × RPMError,
        -5,
        45
    ) ° BTDC
```

### 6.6 Cooling calculations

```text
ECT1Temp = ectVoltageToTemp(ECT1Voltage)
ECT2Temp = ectVoltageToTemp(ECT2Voltage)
SensorDifference = abs(ECT1Temp - ECT2Temp)
SensorDisagreement = 1 when SensorDifference > 15 °C; otherwise 0
ControlTemperature = max(ECT1Temp, ECT2Temp)
```

Main safety branches:

```text
if EmergencyStop = 1 or BatteryVoltage < 8.0 V:
    FanDuty = 0
    WaterPumpDuty = 0
else if SensorDisagreement = 1:
    FanDuty = 100
    WaterPumpDuty = 100
else:
    use the normal maps below
```

PWM fan duty:

```text
if ControlTemperature < 88 °C:
    FanDuty = 0
else if ControlTemperature < 95 °C:
    FanDuty = 20 + (ControlTemperature - 88) × (30 / 7)
else if ControlTemperature < 105 °C:
    FanDuty = 50 + (ControlTemperature - 95) × 5
else:
    FanDuty = 100

if ACRequest = 1 and EngineState >= CRANK:
    FanDuty = max(FanDuty, 35)

FanDuty = clip(FanDuty, 0, 100)
```

Virtual electric-water-pump duty:

```text
if EngineState = RUN:
    if ControlTemperature < 50 °C:
        WaterPumpDuty = 35
    else if ControlTemperature < 90 °C:
        WaterPumpDuty = 35 + (ControlTemperature - 50) × (35 / 40)
    else if ControlTemperature < 110 °C:
        WaterPumpDuty = 70 + (ControlTemperature - 90) × 1.5
    else:
        WaterPumpDuty = 100
else if EngineState is not RUN and ControlTemperature > 95 °C:
    WaterPumpDuty = 60
else:
    WaterPumpDuty = 0

WaterPumpDuty = clip(WaterPumpDuty, 0, 100)
CoolingLoopActive = 1 if FanDuty > 0 or WaterPumpDuty > 0; otherwise 0
```

---

## 7. Required outputs and categories

The application must explicitly distinguish four data categories.

### Measured/status inputs

- Battery voltage
- Engine speed
- Throttle position
- Manifold pressure
- Oxygen-sensor voltage
- ECT1 voltage
- ECT2 voltage
- Accessory load
- Ignition, authorisation, A/C and emergency statuses

### ECU-calculated values

- ECT1 temperature
- ECT2 temperature
- Sensor difference
- Control temperature
- Engine load
- Lambda estimate
- STFT/equivalent fuel correction
- Warm-up enrichment
- Battery compensation
- Base injector pulse width
- Target idle RPM
- RPM error

### Commanded outputs

- Final injector pulse width
- Idle-control duty
- Ignition timing
- Fan duty
- Virtual water-pump duty
- Fuel-pump state
- Starter state
- Injection enable
- Ignition enable

### Operating statuses

- Engine state
- Start permitted
- Closed-loop active
- Idle active
- Cooling-loop active
- ECT sensor disagreement

Every displayed value must show its unit, category and plain-language meaning.

---

## 8. Required page layout

### 8.1 Header

Show:

- page title: **Engine Live-Data Demonstration**;
- one-sentence purpose;
- educational disclaimer;
- run/pause/reset controls;
- current simulation time;
- data-export control.

### 8.2 Input panel

Place student-adjustable inputs in a fixed or easily accessible panel. Group them as:

1. **Power and engine signals** — battery, RPM, TPS, MAP and accessory load.
2. **Fuel feedback** — oxygen-sensor voltage.
3. **Cooling sensors** — ECT1 voltage and ECT2 voltage.
4. **Operating controls** — ignition, fingerprint authorised, A/C request, start, stop and emergency stop.

Show the accepted capped value when it differs from the typed value.

### 8.3 Main system views

Provide an overview plus four tabs or sections:

1. **Fuel and injection**
2. **Idle and ignition**
3. **Cooling**
4. **Start and run**

Each system view must contain:

- a simple dependency flow;
- current measured inputs;
- ECU-calculated values;
- output commands;
- status lamps/badges;
- a short live explanation sentence;
- a trend graph for the relevant signals.

### 8.4 Required dependency flows

Display these flows visually:

```text
O₂ voltage → Lambda estimate → STFT → Injector pulse width

ECT1 temperature + actual RPM + accessory load
→ Target idle and RPM error
→ Idle duty and ignition timing

ECT1 + ECT2 → Sensor plausibility + control temperature
→ Fan duty + virtual pump duty

Authorisation + ignition + start request + battery + RPM
→ Engine state
→ Fuel pump + starter + injection + ignition enable
```

### 8.5 Engine-state display

Show a horizontal stepper or state diagram:

```text
OFF → PRIME → CRANK → RUN → SHUTDOWN
```

Highlight the active state and display elapsed time in that state.

### 8.6 Trend history

Keep at least the most recent **60 seconds** of virtual data. Graphs should use readable labels and units. Reuse the platform's chart library when available.

Recommended series:

- Fuel: O₂ voltage, lambda, STFT and injector pulse width.
- Idle: actual RPM, target RPM, idle duty and ignition timing.
- Cooling: ECT1, ECT2, fan duty and pump duty.
- Start/run: engine-state code, fuel pump, starter, injection enable and ignition enable.

### 8.7 Export

Allow export of current history as CSV. Include simulation time, all accepted inputs, all calculated values and all outputs.

---

## 9. Presets

Add these optional demonstration presets. Loading a preset changes sensor/operating inputs but must not bypass the normal state machine.

### Warm idle

```text
Battery 13.8 V
RPM 800
TPS 2 %
MAP 35 kPa
O₂ 0.45 V
ECT1 1.0 V
ECT2 1.1 V
Accessory load 10 %
A/C OFF
```

### Lean oxygen response

Same as warm idle, but O₂ = 0.10 V.

### High cooling demand

```text
Battery 13.8 V
RPM 900
TPS 3 %
MAP 38 kPa
O₂ 0.45 V
ECT1 0.55 V
ECT2 0.62 V
Accessory load 20 %
A/C ON
```

### Idle load disturbance

```text
Battery 13.0 V
RPM 620
TPS 2 %
MAP 45 kPa
O₂ 0.45 V
ECT1 1.0 V
ECT2 1.1 V
Accessory load 80 %
A/C ON
```

### ECT sensor disagreement

Use ECT1 = 1.0 V and ECT2 = 2.0 V so the temperature difference exceeds 15 °C and the virtual fail-safe sets fan and pump commands to 100%.

---

## 10. Explanatory text behaviour

Generate short statements from the current values. Examples:

- “The low oxygen-sensor voltage represents a lean indication; the calculated positive fuel correction increases injector pulse width.”
- “Actual RPM is below the coolant-dependent target; idle-control duty increases to reduce the speed error.”
- “ECT1 and ECT2 disagree by more than 15 °C; the virtual cooling logic commands full fan and pump duty.”
- “The start request is blocked because fingerprint authorisation is not active.”

Do not state that simplified signals are real OEM scan-tool values.

---

## 11. Validation and acceptance criteria

The feature is complete only when:

1. all inputs are capped at the defined limits;
2. students cannot edit calculated values or commanded outputs;
3. all four systems use the exact equations and state logic above;
4. the state sequence respects prime, crank, run and shutdown timing;
5. graphs update while simulation is running;
6. pause stops virtual time without losing state;
7. reset returns the application to OFF and clears history;
8. emergency stop forces shutdown and remains latched until reset;
9. CSV export contains the displayed data;
10. the app works without MATLAB and without a network API;
11. automated tests cover the cases in `ACCEPTANCE_TESTS.md`;
12. the page clearly states that the model is educational and not an OEM calibration;
13. there is no physical-versus-virtual comparison feature;
14. the implementation passes the repository's available lint, type-check, test and build commands;
15. it is one section inside the existing platform, reached through its established routing and navigation, with its existing components, styles and state conventions;
16. no new platform/project/deployment or unrelated redesign has been introduced;
17. navigation to and from existing sections still works, and simulation timers/subscriptions are cleaned up on leaving the feature;
18. the UI clearly identifies virtual ECT1/ECT2, the duty-controlled fan and the virtual electric water pump, states that the physical 1NZ setup has no electric water pump, and keeps the two stages' tests independent with no comparison.

---

## 12. Delivery requirements

After implementation:

1. List every file created or changed.
2. Explain where the pure model logic is located.
3. Explain how to run the page locally.
4. Explain how to run tests.
5. State any existing project conventions that required a change from the suggested route or file names.
6. Do not leave placeholder calculations, mocked outputs or TODO comments for any required system.
7. Do not silently simplify, omit or recalibrate a signal. If a repository constraint prevents an engineering requirement, report the affected requirement and request the information needed to resolve it; preserve the specified model while completing unaffected integration work.
8. Report the reused routing/components/styles/state conventions, the section's actual navigation location, and the results of the model and host-platform checks. Distinguish checks actually run from checks blocked or still pending.
9. Deliver the section through the existing repository's normal development workflow. The retained standalone prototype is reference material, not the delivered platform.
