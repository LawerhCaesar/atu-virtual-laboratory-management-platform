# CODEX IMPLEMENTATION TASK

## Engine–Generator Fuel-to-Electric Virtual Laboratory Module

### Project identifiers

- **Project title:** Modelling and Testing Engine–Generator Fuel-to-Electric Energy Conversion for Series-Based Hybrid Vehicle for Virtual-Platform Integration
- **Authoritative Simulink model:** `EngineGenerator_FuelToElectric_SelfContained.slx`
- **Model data guide:** `EngineGenerator_Model_Input_Data_and_Operating_Guide.docx`
- **Conversation context link:** `https://chatgpt.com/share/PASTE-SHARED-CHAT-LINK-HERE`
- **Important:** Replace the placeholder conversation URL with the shared ChatGPT link before handing this task to Codex. If the link is unavailable, this implementation file is the authoritative specification and contains all logic needed to proceed.

---

## 1. Mission

Convert the supplied engine–generator Simulink concept into a maintainable programming-language implementation that can be integrated into the existing virtual laboratory and operated through a clear, user-friendly interface.

The completed module must:

1. reproduce the fuel-to-electric calculation logic of the Simulink model without requiring MATLAB or Simulink at runtime;
2. allow a user to change operating parameters and immediately see their effect;
3. support both complete scenario simulation and step-by-step streaming operation;
4. preserve the model boundary from fuel input to generator electrical output;
5. expose standard outputs for integration with battery, energy-management, vehicle-demand and other virtual-laboratory modules;
6. provide scientific plots, summary values and an animated visual explanation of the energy flow; and
7. remain simple enough for students and researchers to understand, inspect and modify.

Do not build a second standalone application when an existing platform repository is present. Inspect the repository first, follow its established architecture, components, design system, routing, state management, testing conventions and deployment method, then add this module natively.

---

## 2. Repository-first implementation rule

Before coding:

1. inspect the current repository structure and determine the frontend, backend, numerical and charting technologies already in use;
2. reuse existing components and patterns rather than introducing a parallel framework;
3. identify how other scientific modules receive inputs, run calculations, display charts and export results;
4. implement one authoritative engine–generator calculation core with no duplicated equations in the user interface; and
5. document any unavoidable deviation from the existing project conventions.

### Fallback stack only when no platform stack exists

Use a browser-capable implementation with:

- a framework-independent TypeScript numerical core;
- a React user interface;
- a Web Worker for long simulations if necessary;
- the repository’s preferred charting library, or a mature compatible chart library if none exists; and
- an optional API adapter only when the wider platform requires a server-side interface.

The model is computationally light and may run entirely in the browser. Do not create a backend merely to reproduce calculations that can be performed safely and deterministically in the client. If the existing platform already has a numerical backend, implement the same model core in that backend’s language and expose a typed adapter to the frontend.

---

## 3. Scientific boundary

The model begins with operating inputs and fuel properties and ends at the generator electrical output.

### Included

- user-defined electrical demand;
- steady, gradual and pulsed demand profiles;
- external battery state of charge as an operating condition;
- a simple SOC support request;
- generator rating limitation;
- enable/disable command;
- one-second command delay;
- generator power ramp limitation;
- normalized generator efficiency map;
- normalized engine-speed map;
- normalized BSFC map;
- engine shaft power and torque;
- fuel mass-flow rate and fuel chemical power;
- engine, generator and complete fuel-to-electric efficiencies;
- engine, generator and total conversion losses;
- generator utilization;
- electrical demand shortfall;
- energy balance residual;
- cumulative electrical energy, fuel energy, conversion loss, shortfall energy and fuel mass.

### Excluded

- battery voltage, current, temperature, ageing and electrochemistry;
- traction motor and inverter switching;
- transmission and wheel torque;
- vehicle acceleration, speed, road load and range;
- regenerative braking and friction-brake allocation;
- emissions and after-treatment;
- production ECU calibration; and
- development of the overall virtual-laboratory platform.

Do not silently introduce excluded physics. Any future connection to those functions must occur through documented interfaces.

---

## 4. User inputs

Implement the following basic inputs on the main interface. Each control must have a numeric field, unit, valid range, default value, tooltip and reset-to-default action.

| Field | Type | Unit | Default | Recommended range | Meaning |
|---|---:|---:|---:|---:|---|
| `meanLoadKW` | number | kW | 18 | 0–45 | Mean electrical demand requested from the generating set. |
| `demandProfileId` | enum | – | 2 | 1, 2 or 3 | 1 = steady, 2 = gradual, 3 = pulsed. |
| `batterySocPct` | number | % | 60 | 10–95; hard limit 0–100 | External battery SOC used only by the simple support rule. |
| `generatorRatingKW` | number | kW | 30 | 10–60; must be positive | Continuous generator electrical output limit. |
| `enabled` | boolean | – | true | false/true | Turns the generating set command off or on. |
| `fuelLhvMJPerKg` | number | MJ/kg | 43 | positive; use traceable fuel data | Fuel lower heating value. |
| `simulationDurationS` | number | s | 120 | positive | Duration of a scenario run. |
| `timeStepS` | number | s | 0.1 | positive; normally 0.01–1.0 | Fixed simulation time step. |

### Advanced settings

Place the following in a collapsed **Advanced Settings** section. The user must be able to edit them, restore defaults and save a scenario.

| Setting | Default | Unit |
|---|---:|---:|
| `demandLimitKW` | 45 | kW |
| `socTargetPct` | 60 | % |
| `socSupportGainKWPerPct` | 0.15 | kW/% |
| `maxSocSupportKW` | 6 | kW |
| `commandDelayS` | 1 | s |
| `rampUpKWPerS` | 8 | kW/s |
| `rampDownKWPerS` | 12 | kW/s |
| `maxMapLoadFraction` | 1.25 | – |
| `powerEpsilonKW` | 0.001 | kW |
| `efficiencyEpsilon` | 0.05 | – |
| `speedEpsilonRPM` | 1 | rpm |

---

## 5. Built-in normalized component maps

Use piecewise-linear interpolation with clipping at the first and last breakpoint. Store these data in one clearly named configuration object. Do not scatter the values throughout the code.

```text
loadFraction = [0.00, 0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 1.00, 1.25]

generatorEfficiency = [0.70, 0.76, 0.82, 0.87, 0.90, 0.92, 0.93, 0.92, 0.89]

engineSpeedRPM = [0, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]

bsfcGPerKWh = [400, 340, 300, 270, 250, 240, 235, 238, 250]
```

Provide a secondary **Component Data** view where an advanced user can:

- inspect the maps;
- replace map values through a validated table or JSON/CSV import;
- restore the demonstration maps;
- see the source/description/version fields; and
- receive a warning when array lengths differ, breakpoints are not strictly increasing, efficiency is outside 0–1, speed is negative or BSFC is non-positive.

The main interface should remain uncluttered; map editing belongs in the advanced view.

---

## 6. Exact demand profiles

At time `t` in seconds:

### Profile 1: steady

```text
P_demand(t) = meanLoadKW
```

### Profile 2: gradual

```text
P_demand(t) = meanLoadKW × [1 + 0.25 × sin(2πt / 60)]
```

### Profile 3: pulsed

Use a 20-second period and 50% duty cycle. The pulse equals 1 for the first 10 seconds of each period and 0 for the next 10 seconds.

```text
pulse(t) = 1 when (t mod 20) < 10, otherwise 0
P_demand(t) = meanLoadKW × [0.60 + 0.80 × pulse(t)]
```

Finally:

```text
P_demand(t) = clamp(P_demand(t), 0, demandLimitKW)
```

---

## 7. Exact model equations and execution order

Use SI-compatible units as stated. Preserve the sequence below because delay, ramping and saturation affect the results.

### 7.1 SOC support request

```text
P_SOC = clamp[
  socSupportGainKWPerPct × (socTargetPct − batterySocPct),
  0,
  maxSocSupportKW
]
```

SOC is an external condition. Do not calculate SOC change inside this model.

### 7.2 Unrestricted and limited command

```text
P_cmd_raw = P_demand + P_SOC

P_cmd_limited = min(
  max(P_cmd_raw, 0),
  generatorRatingKW
) × (enabled ? 1 : 0)
```

### 7.3 Command delay

Apply a transport delay equal to `commandDelayS` to `P_cmd_limited`.

For a fixed-step implementation, use a timestamped FIFO/ring buffer. When the delay is not an exact multiple of the time step, linearly interpolate between stored samples. Before sufficient history exists, return zero.

### 7.4 Rate limiter

For previous command `P_cmd_previous` and delayed target `P_cmd_target`:

```text
increaseLimit = rampUpKWPerS × timeStepS
decreaseLimit = rampDownKWPerS × timeStepS
change = clamp(P_cmd_target − P_cmd_previous, −decreaseLimit, increaseLimit)
P_cmd = P_cmd_previous + change
```

### 7.5 Normalized load fraction

```text
safeRating = max(generatorRatingKW, powerEpsilonKW)
u = clamp(P_cmd / safeRating, 0, maxMapLoadFraction)
```

Interpolate the three built-in maps at `u`:

```text
eta_gen = interpolate(u, loadFraction, generatorEfficiency)
n_eng_rpm = interpolate(u, loadFraction, engineSpeedRPM)
BSFC = interpolate(u, loadFraction, bsfcGPerKWh)
```

### 7.6 Engine shaft power

```text
safeEtaGen = max(eta_gen, efficiencyEpsilon)
P_shaft_kW = P_cmd / safeEtaGen
```

### 7.7 Engine torque

```text
safeEngineSpeedRPM = max(n_eng_rpm, speedEpsilonRPM)
T_eng_Nm = 9550 × P_shaft_kW / safeEngineSpeedRPM
```

### 7.8 Fuel flow and fuel chemical power

```text
fuelFlowGPS = BSFC × P_shaft_kW / 3600
P_fuel_kW = fuelFlowGPS × fuelLhvMJPerKg
safeFuelPowerKW = max(P_fuel_kW, powerEpsilonKW)
```

The unit conversion is intentional: `g/s × MJ/kg = kJ/s = kW`.

### 7.9 Generator electrical output

```text
P_gen_unrestricted_kW = P_shaft_kW × eta_gen
P_gen_kW = min(P_gen_unrestricted_kW, generatorRatingKW)
```

### 7.10 Efficiencies

```text
eta_engine = P_shaft_kW / safeFuelPowerKW
eta_f2e = P_gen_kW / safeFuelPowerKW
```

### 7.11 Losses

```text
P_engine_loss_kW = P_fuel_kW − P_shaft_kW
P_generator_loss_kW = P_shaft_kW − P_gen_kW
P_total_loss_kW = P_fuel_kW − P_gen_kW
```

### 7.12 Utilization and shortfall

```text
generatorUtilisationPct = 100 × P_gen_kW / safeRating
P_shortfall_kW = max(P_demand − P_gen_kW, 0)
```

Shortfall is measured against the immediate external electrical demand, not the additional SOC support request.

### 7.13 Energy-balance residual

```text
energyResidualKW =
  P_fuel_kW
  − P_engine_loss_kW
  − P_generator_loss_kW
  − P_gen_kW
```

The residual should be numerically close to zero.

### 7.14 Cumulative quantities

Integrate using the trapezoidal rule, unless the existing platform has a standard integrator that is demonstrably equivalent.

```text
generatedEnergyKWh = ∫ P_gen_kW dt / 3600
fuelEnergyKWh = ∫ P_fuel_kW dt / 3600
lossEnergyKWh = ∫ P_total_loss_kW dt / 3600
shortfallEnergyKWh = ∫ P_shortfall_kW dt / 3600
totalFuelG = ∫ fuelFlowGPS dt
```

---

## 8. Model state and public programming interface

Implement one pure numerical core with no UI imports.

The core must support both methods below.

### Complete scenario

```text
simulate(config, maps?) -> SimulationResult
```

### Streaming/step mode

```text
initialize(config, maps?) -> ModelState
step(state, externalInput, dt) -> { state, sample }
reset(state, config) -> ModelState
```

This allows the same calculation core to power:

- a complete 120-second experiment;
- a live animated interface;
- an external vehicle-demand model;
- an API endpoint; and
- later virtual-platform integration.

### Minimum typed data contract

Adapt syntax to the repository language, but preserve these concepts:

```ts
export type DemandProfileId = 1 | 2 | 3;

export interface EngineGeneratorInputs {
  meanLoadKW: number;
  demandProfileId: DemandProfileId;
  batterySocPct: number;
  generatorRatingKW: number;
  enabled: boolean;
  fuelLhvMJPerKg: number;
  simulationDurationS: number;
  timeStepS: number;
}

export interface EngineGeneratorSettings {
  demandLimitKW: number;
  socTargetPct: number;
  socSupportGainKWPerPct: number;
  maxSocSupportKW: number;
  commandDelayS: number;
  rampUpKWPerS: number;
  rampDownKWPerS: number;
  maxMapLoadFraction: number;
  powerEpsilonKW: number;
  efficiencyEpsilon: number;
  speedEpsilonRPM: number;
}

export interface EngineGeneratorMaps {
  loadFraction: number[];
  generatorEfficiency: number[];
  engineSpeedRPM: number[];
  bsfcGPerKWh: number[];
  source?: string;
  version?: string;
}

export interface EngineGeneratorSample {
  timeS: number;
  demandKW: number;
  socSupportKW: number;
  commandRawKW: number;
  commandKW: number;
  loadFraction: number;
  engineSpeedRPM: number;
  engineTorqueNm: number;
  shaftPowerKW: number;
  bsfcGPerKWh: number;
  fuelFlowGPS: number;
  fuelPowerKW: number;
  engineEfficiencyRatio: number;
  generatorEfficiencyRatio: number;
  generatorPowerKW: number;
  fuelToElectricEfficiencyRatio: number;
  engineLossKW: number;
  generatorLossKW: number;
  totalLossKW: number;
  generatorUtilisationPct: number;
  demandShortfallKW: number;
  energyResidualKW: number;
  generatedEnergyKWh: number;
  fuelEnergyKWh: number;
  lossEnergyKWh: number;
  shortfallEnergyKWh: number;
  totalFuelG: number;
  status: 'OFF' | 'DELAYED' | 'RAMPING' | 'GENERATING' | 'LIMITED' | 'INVALID_INPUT';
}

export interface SimulationSummary {
  generatedEnergyKWh: number;
  fuelEnergyKWh: number;
  lossEnergyKWh: number;
  shortfallEnergyKWh: number;
  totalFuelG: number;
  caseFuelToElectricEfficiencyPct: number;
  averageGeneratorUtilisationPct: number;
  maximumGeneratorPowerKW: number;
  maximumDemandShortfallKW: number;
  maximumAbsoluteEnergyResidualKW: number;
}

export interface SimulationResult {
  inputs: EngineGeneratorInputs;
  settings: EngineGeneratorSettings;
  maps: EngineGeneratorMaps;
  samples: EngineGeneratorSample[];
  summary: SimulationSummary;
  warnings: string[];
}
```

### Platform-compatible root outputs

Expose these exact signal names through the platform adapter because they match the current Simulink model:

- `P_gen_kW`
- `eta_f2e_ratio`
- `fuel_flow_gps`
- `P_shortfall_kW`
- `generator_utilisation_pct`

Additional outputs may be exposed, but do not rename the five core signals without an adapter.

---

## 9. Input validation and numerical safeguards

The interface and core must reject or clearly warn about invalid values.

Mandatory checks:

- all numeric values must be finite;
- duration and time step must be positive;
- generator rating and fuel LHV must be positive;
- SOC hard limit is 0–100%;
- profile must be 1, 2 or 3;
- map arrays must have equal lengths;
- load-fraction breakpoints must be strictly increasing;
- efficiencies must remain between 0 and 1;
- engine speed cannot be negative;
- BSFC must be positive;
- calculations must not return `NaN` or infinity; and
- a warning must be shown when the user enters values outside the recommended study range even if the value remains mathematically valid.

Do not hide clipping or rating limits. Show the user when a limit is active.

---

## 10. User interface requirements

Build one clear experiment page or module inside the existing virtual laboratory.

### Recommended desktop layout

1. **Left panel — Experiment Setup**
   - six basic inputs;
   - duration and time step;
   - profile selector with plain-language labels;
   - Run, Pause/Resume if live mode exists, Reset and Restore Defaults;
   - Save Scenario and Load Scenario;
   - collapsed Advanced Settings;
   - collapsed Component Data/maps.

2. **Centre panel — Animated Energy Flow**
   - a clean side-view hybrid vehicle silhouette or engineering schematic;
   - fuel tank, engine, generator and DC-link/battery connection;
   - animated arrows from fuel to engine, engine to generator and generator to DC link;
   - arrow thickness or speed proportional to power;
   - engine and generator icons indicating OFF, DELAYED, RAMPING, GENERATING or LIMITED;
   - battery SOC gauge based on the external SOC input;
   - visible rating-limit and demand-shortfall warnings.

3. **Right panel — Live Results**
   - generated power;
   - fuel-to-electric efficiency;
   - fuel-flow rate;
   - generator utilization;
   - demand shortfall;
   - total fuel used;
   - generated energy;
   - status badge.

4. **Bottom panel — Scientific Results**
   - Power chart: demand, command, generated power and shortfall;
   - Efficiency chart: engine, generator and fuel-to-electric efficiency, plus utilization;
   - Engine chart: speed, torque, shaft power and fuel flow;
   - Loss chart: engine loss, generator loss, total loss and residual;
   - Cumulative chart: generated energy, fuel energy, loss energy, shortfall energy and total fuel.

Provide tooltips, legends, units, axis labels, zoom/hover inspection and an option to show/hide series. The layout must be responsive and usable on common laptop screens. On a small screen, stack the input, visual and results sections vertically.

### Accessibility

- all controls must have associated labels;
- do not communicate status by color alone;
- charts require readable legends and text summaries;
- animation must respect reduced-motion settings;
- keyboard navigation must work; and
- contrast must be sufficient for normal use.

---

## 11. Animated car recommendation and scientific restriction

A physically moving car animation is **not required by this model** because the engine–generator module does not calculate vehicle speed, wheel torque or longitudinal motion.

The scientifically appropriate primary visual is:

> **A stationary vehicle silhouette containing an animated fuel → engine → generator → DC-link/battery energy path.**

This gives the user an intuitive vehicle context without pretending that the model predicts vehicle movement.

A road-moving car animation may be added only in one of these forms:

1. **Illustrative mode:** clearly label it as a visual illustration driven by demand profile rather than calculated vehicle speed; or
2. **Integrated mode:** connect the animation to a real vehicle-speed signal supplied by a separate vehicle-dynamics model.

Do not infer vehicle speed from generator power and present it as a scientific result.

---

## 12. Exports and repeatability

Provide:

- CSV export of the time-series table;
- JSON export containing inputs, settings, maps, warnings, samples and summary;
- image export for each chart when supported by the platform;
- scenario save/load in JSON;
- a concise printable results summary; and
- a copyable integration payload containing the five standard root outputs.

Every exported result must include model version, map version, input values, time step, duration and generation timestamp.

---

## 13. Integration adapter

Keep the numerical core independent from the UI.

If the virtual platform uses direct in-process modules, expose a typed adapter such as:

```text
EngineGeneratorModule.initialize(config)
EngineGeneratorModule.step(externalInput, dt)
EngineGeneratorModule.runScenario(config)
EngineGeneratorModule.getOutputs()
EngineGeneratorModule.reset()
```

If the platform requires an HTTP service, implement the equivalent of:

```text
POST /api/v1/engine-generator/simulate
POST /api/v1/engine-generator/validate
GET  /api/v1/engine-generator/defaults
```

Use the existing platform’s API conventions. Do not add an HTTP layer when direct module integration is already available.

For live integration, accept external values for:

- `P_demand_kW`
- `battery_SOC_pct`
- `generator_rating_kW`
- `enabled`
- `fuel_LHV_MJ_per_kg`

Return at least the five standard root outputs at each step.

---

## 14. Required verification

Implement automated checks in the repository’s normal test structure. Tests may remain internal to the codebase; they do not need to appear as controls on the user interface.

### Baseline case

Use:

```text
meanLoadKW = 18
demandProfileId = 2
batterySocPct = 60
generatorRatingKW = 30
enabled = true
fuelLhvMJPerKg = 43
simulationDurationS = 120
timeStepS = 0.1
all advanced settings = defaults
all maps = built-in maps
```

The converted implementation should produce approximately:

| Result | Reference value | Suggested tolerance |
|---|---:|---:|
| Generated electrical energy | 0.5896 kWh | ±1% |
| Fuel energy supplied | 1.8824 kWh | ±1% |
| Loss energy | 1.2928 kWh | ±1% |
| Shortfall energy | 0.01538 kWh | ±3% |
| Total fuel used | 157.60 g | ±1% |
| Case fuel-to-electric efficiency | 31.32% | ±0.5 percentage point |
| Maximum generated power | 22.50 kW | ±0.05 kW |
| Average generator utilization | 58.96% | ±1 percentage point |
| Maximum absolute energy residual | near 0 | less than 1×10⁻⁹ kW where practical |

Small differences caused by numerical integration are acceptable only when explained.

### Additional required behavior checks

- enable = false gives zero command and generation after the delay/ramp response;
- low SOC adds a positive support request, capped at 6 kW;
- high SOC does not create negative support;
- generator output never exceeds the selected rating;
- gradual and pulsed demand profiles follow the specified equations;
- shortfall becomes positive when demand exceeds generated power;
- increasing generator rating can reduce rating-related shortfall;
- all cumulative outputs are non-decreasing when their instantaneous inputs are non-negative;
- map replacement changes results without changing UI or integration code; and
- invalid input produces a clear error or warning rather than a silent failure.

---

## 15. Code quality requirements

- use descriptive engineering names and explicit units;
- keep equations close to comments or documentation that state the governing relationship;
- avoid hidden “magic numbers”; all constants belong in the settings or maps object;
- no equation may be duplicated in both the core and UI;
- avoid global mutable state;
- make simulations deterministic;
- separate validation, interpolation, simulation state, summary calculation, export and presentation;
- use the repository’s formatter, linter and test runner;
- include concise API documentation and examples; and
- do not claim production-vehicle calibration or full physical validation.

---

## 16. Mandatory final visual output

Do not consider the task complete after implementing only the equations or API.

The final submission must include a working user interface and visual proof of it. Produce the most suitable outputs supported by the repository environment:

1. a desktop screenshot showing the input panel, animated energy-flow vehicle visual, live result cards and charts;
2. a second screenshot showing a changed scenario with visibly different results;
3. a mobile or narrow-screen screenshot showing responsive layout;
4. preferably a short GIF or video showing the energy-flow animation and chart progression during a run; and
5. a short caption explaining what each visual demonstrates.

If automated screenshot capture is unavailable, run the platform locally and provide exact commands plus a clear manual capture checklist. Do not substitute a static mock-up for a working interface.

The visual design must correspond to the scientific model. It should emphasize fuel input, engine shaft conversion, generator electrical output, losses, utilization and shortfall. A decorative moving car by itself is not an acceptable result.

---

## 17. Required completion report from Codex

At completion, report:

- files added or modified;
- the language and architecture used;
- how the model equations were mapped into code;
- how to run the platform locally;
- how to run validation/tests;
- baseline verification results;
- location of screenshots/GIF/video;
- any assumptions or deviations;
- remaining integration work, if any; and
- confirmation that the five standard root outputs are available.

Do not report completion until the numerical core, interactive interface, exports, integration adapter and visual proof are all present and functioning.
