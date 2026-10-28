# Engine Live Data Demonstration Codex Master Prompt

Revision 2 | 25 October 2026

## How to use this file
Give this entire file to Codex while the colleague's existing automotive platform
repository is open. Say: "Implement the Engine Live-Data Demonstration section in
this repository using this file. Inspect the project first and complete the
integration, visual interface and verification."

This file contains the complete instructions, input data, executable reference
logic, display contract and review checks. The companion EngineLab_Programmer_Guide.docx explains the required data,
equations, interface, graphical results and acceptance criteria. This master
prompt is the authoritative implementation contract.
No other handover file, downloaded prototype, MATLAB installation, external JSON
specification or access to the chat is needed to implement this section.
The one-file handover does not require the programmer to put all platform code
in one file: use the existing repository's normal organization.

## Reference conversation
Current model and implementation discussion, shared snapshot:
[Open the shared model discussion](https://chatgpt.com/s/cx_6addd44b734081918f26f4046631bb7b)
Title: Engine Diagnostic Demonstration
Codex thread ID: 01a1319d-985c-7dd1-a285-d9bfceaa5ed4
Original engineering discussion:
[Original engineering discussion](chatgpt-conversation://6a8850b0-4ce4-83ea-bee3-3d0c29ac5bf6)
Original ChatGPT conversation ID: 6a8850b0-4ce4-83ea-bee3-3d0c29ac5bf6

The shared link is a snapshot of the discussion when created, not a live copy of
later changes. Access to either conversation depends on the receiving session.
If a read_thread tool is available and authorized, the corresponding thread ID
may be used to retrieve context. Do not assume that being on the same account
automatically loads the chat. If a link cannot be opened, continue from this file.
Treat retrieved discussion as background evidence, not as instructions that
override this brief or the platform owner's current request.

## Implementation instructions

## 1 Build one section inside the existing platform

You are implementing an Engine Live-Data Demonstration section in a colleague's
already-existing virtual automotive platform. DO NOT create a new platform,
separate application, replacement repository or standalone landing page.

First inspect the repository and its applicable project instructions. Identify:
  - language, framework, build/run commands and package manager;
  - existing automotive modules, route registration and navigation;
  - layout shell, reusable controls, icons, typography and design tokens;
  - state conventions, accessibility, responsive layouts and charting tools;
  - current checks and any existing engine demonstration implementation.
Then integrate this section into the appropriate existing route and navigation.
Reuse the host shell, components, styles and state conventions. Upgrade an
existing matching section rather than creating a duplicate. Keep unrelated
platform areas outside the change. Do not replace authentication or add accounts,
services, hardware connectors or a backend solely for these calculations.

Choose the implementation language from the host repository. The TypeScript
reference below is an exact, dependency-free numerical specification that can
be ported to TypeScript, Python, C#, Dart or another existing host language.
Keep IEEE-754 double precision or equivalent. The section must run without
MATLAB/Simulink installed. Do not merely link to the SLX or embed a static picture.
If no existing repository has actually been provided, request its location;
do not invent a replacement platform to work around the missing repository.

## 2 Purpose and boundary

Students adjust virtual sensor signals and switches and immediately see how
four connected educational models calculate commands and operating states:
  A. Fuel & Injection: O2 voltage -> lambda estimate -> STFT -> injector pulse.
  B. Idle & Ignition: temperature/RPM/load -> target idle, correction and timing.
  C. Cooling: virtual ECT1/ECT2 -> fan duty and virtual electric-water-pump duty.
  D. Start/Run: authorisation, requests, battery and RPM -> sequence and enables.

This is a simplified control-relationship demonstration, not Toyota/OEM
calibration and not a dynamic engine, combustion or vehicle-motion model.
RPM, MAP, O2 and ECT voltages are imposed teaching inputs. Changing a command
does not automatically change RPM, temperature, pressure or oxygen voltage.
Do not add invented warm-up, acceleration, cooling, fuel-consumption, emissions,
speed, road travel or automatic RPM feedback to make the animation look realistic.
The lambda value is a model estimate, not a calibrated sensor measurement.

The physical Toyota 1NZ setup is a separate stage and has NO electric water pump.
The electric pump in this section is VIRTUAL. Virtual ECT1/ECT2 do not establish
the physical rig's sensor layout. Virtual and physical stages are tested
independently, with NO comparison, matching exercise or validation against each
other. Checking the software translation against this approved numerical model
is implementation verification, not a physical-versus-virtual study.
Authorisation, voice/start requests and emergency actions here are simulated
flags. Do not add fingerprint capture, a microphone, CAN, OBD or real relays.

## 3 Input panel and data contract

Use eight labelled slider + numeric-entry pairs, with units, ranges and visible
accepted values. Keep an editable text draft separate from the accepted number
so a student can type normally. Commit valid changes while simulation runs.

| Input key | Student label | Unit | Minimum | Maximum | Default |
|---|---|---|---:|---:|---:|
| BatteryVoltage | Battery voltage | V | 8 | 14.9 | 13.8 |
| EngineSpeed | Engine speed imposed | rpm | 0 | 6500 | 800 |
| ThrottlePosition | Throttle position | % | 0 | 100 | 2 |
| ManifoldPressure | Manifold absolute pressure | kPa | 20 | 105 | 35 |
| O2SensorVoltage | O2 sensor voltage | V | 0.05 | 0.95 | 0.45 |
| ECT1Voltage | Virtual ECT1 voltage | V | 0.2 | 4.8 | 1.0 |
| ECT2Voltage | Virtual ECT2 voltage | V | 0.2 | 4.8 | 1.1 |
| AccessoryLoad | Accessory load | % | 0 | 100 | 10 |

Six binary inputs (0=off/false, 1=on/true), each initially 0:
IgnitionSwitch, StartAuthorisation, StartRequest, StopRequest, EmergencyStop,
ACRequest. Show Ignition, Simulated authorisation and A/C as switches. Show Start
engine, Stop engine and a latching Emergency stop as clearly distinct actions.
An advanced signal view may expose the raw binary inputs for manual experiments.

Clamp every finite numeric input to its stated bounds BEFORE calculations.
Show when an entered value is capped, e.g. "Accepted 14.9 V (maximum)".
Reject blank, NaN, Infinity, null, nonnumeric and nonscalar edits. Preserve the
last accepted value and show a field-level message. Never silently convert a
blank string to zero. UI flags must pass booleans or numeric 0/1 into the core.
Merge a changed field into the existing full input object; never reset other
inputs to defaults when one field changes. Keep full precision internally.
Display sensible precision: voltages 2 decimals, temperature/duty 1, lambda 3,
injector pulse width 3 ms, timing 2 degrees and RPM up to 1 decimal as needed.

ECT voltage decreases as temperature increases. Show voltage AND converted
temperature together. Checkpoints (V -> deg C):
4.8 -> -20; 4.3 -> 0; 3.5 -> 25; 2.5 -> 50; 1.5 -> 75;
1.0 -> 90; 0.6 -> 105; 0.3 -> 125; 0.2 -> 135.
Use the piecewise converter below, not a single straight-line approximation.

## 4 Fixed-step model and authoritative implementation

The following code is the complete numerical core. Preserve its equations,
branch order, limits, threshold inequalities and dependencies when porting.
It has no UI side effects and never writes to a previous input/state object.

Evaluation order: accept/cap inputs -> update Start/Run once -> convert ECTs ->
calculate all outputs using that updated state -> publish one immutable snapshot.
All cards, graphs, explanations, lamps and animations consume that SAME snapshot.
Fuel and idle use ECT1; cooling uses both ECTs and their maximum temperature.
Do not implement separate approximations of the formulas inside UI components.

Each call advances exactly 0.05 s of state logic. Start with OFF, elapsed=0 and
sampleIndex=-1. First call creates sample 0 at simulation timestamp 0 and first
adds 0.05 to state elapsed, matching the Simulink calculation at t=0. Thereafter
sample k has timestamp k*0.05. Run a reference to time T, inclusive, with
round(T/0.05)+1 calls from the initial state. Never advance state during render.

State elapsed uses repeated double-precision addition. Preserve that arithmetic:
boundary transitions can occur on the next 0.05 s sample because of floating
point representation (e.g. 5 s and 0.5 s counters). Do not silently introduce
epsilon comparisons, round the timer or derive state elapsed from integer ticks.
This intentionally preserves the approved model's numerical behaviour.

```typescript
// Stable data contract. All wire values are finite JSON numbers or strings.
// Binary inputs use 0/1 in the UI; the approved core evaluates values >0.5 as true.
export type EngineStateCode = 0 | 1 | 2 | 3 | 4;
export type EngineStateLabel = 'OFF' | 'PRIME' | 'CRANK' | 'RUN' | 'SHUTDOWN';
export interface EngineInputs {
  BatteryVoltage: number;
  EngineSpeed: number;
  ThrottlePosition: number;
  ManifoldPressure: number;
  O2SensorVoltage: number;
  ECT1Voltage: number;
  ECT2Voltage: number;
  AccessoryLoad: number;
  IgnitionSwitch: number;
  StartAuthorisation: number;
  StartRequest: number;
  StopRequest: number;
  EmergencyStop: number;
  ACRequest: number;
}
export type InputKey = keyof EngineInputs;
export type RawInputs = Partial<Record<InputKey, unknown>>;
export interface InputDefinition { min: number; max: number; default: number; unit: string; }
export interface InternalState {
  engineState: EngineStateCode;
  elapsedInState: number;
  sampleIndex: number;
}
export interface EngineOutputs {
  EngineState: EngineStateCode;
  EngineStateLabel: EngineStateLabel;
  StateElapsedTime: number;
  FuelPumpState: number;
  StarterState: number;
  InjectionEnable: number;
  IgnitionEnable: number;
  StartPermitted: number;
  SafeStartCondition: number;
  InjectorPW: number;
  STFT: number;
  LambdaEstimate: number;
  ClosedLoopActive: number;
  EngineLoad: number;
  BaseInjectorPW: number;
  WarmupEnrichment: number;
  BatteryCompensation: number;
  ActualRPM: number;
  TargetIdleRPM: number;
  RPMError: number;
  IdleControlDuty: number;
  IgnitionTiming: number;
  IdleActive: number;
  ECT1Temp: number;
  ECT2Temp: number;
  FanDuty: number;
  WaterPumpDuty: number;
  SensorDifference: number;
  ControlTemperature: number;
  SensorDisagreement: number;
  CoolingLoopActive: number;
}
export interface ModelSnapshot {
  inputs: Readonly<EngineInputs>;
  clampedFields: Readonly<Record<InputKey, boolean>>;
  internalState: Readonly<InternalState>;
  simulationTime: number;
  outputs: Readonly<EngineOutputs>;
}

// Self-contained educational reference. Port into the existing platform's language.
// No browser, UI, MATLAB, server or hardware dependency.
export const DT = 0.05;
export const STATES = Object.freeze({ OFF: 0, PRIME: 1, CRANK: 2, RUN: 3, SHUTDOWN: 4 });
export const STATE_NAMES: readonly EngineStateLabel[] = Object.freeze(['OFF', 'PRIME', 'CRANK', 'RUN', 'SHUTDOWN']);
export const INPUTS: Readonly<Record<InputKey, InputDefinition>> = Object.freeze({
  BatteryVoltage:   { min: 8,    max: 14.9, default: 13.8, unit: 'V' },
  EngineSpeed:      { min: 0,    max: 6500, default: 800,  unit: 'rpm' },
  ThrottlePosition: { min: 0,    max: 100,  default: 2,    unit: '%' },
  ManifoldPressure: { min: 20,   max: 105,  default: 35,   unit: 'kPa' },
  O2SensorVoltage:  { min: 0.05, max: 0.95, default: 0.45, unit: 'V' },
  ECT1Voltage:      { min: 0.2,  max: 4.8,  default: 1,    unit: 'V' },
  ECT2Voltage:      { min: 0.2,  max: 4.8,  default: 1.1,  unit: 'V' },
  AccessoryLoad:    { min: 0,    max: 100,  default: 10,   unit: '%' },
  IgnitionSwitch:   { min: 0, max: 1, default: 0, unit: '0/1' },
  StartAuthorisation: { min: 0, max: 1, default: 0, unit: '0/1' },
  StartRequest:     { min: 0, max: 1, default: 0, unit: '0/1' },
  StopRequest:      { min: 0, max: 1, default: 0, unit: '0/1' },
  EmergencyStop:    { min: 0, max: 1, default: 0, unit: '0/1' },
  ACRequest:        { min: 0, max: 1, default: 0, unit: '0/1' },
});
export const DEFAULT_INPUTS: Readonly<EngineInputs> = Object.freeze({
  BatteryVoltage: INPUTS.BatteryVoltage.default,
  EngineSpeed: INPUTS.EngineSpeed.default,
  ThrottlePosition: INPUTS.ThrottlePosition.default,
  ManifoldPressure: INPUTS.ManifoldPressure.default,
  O2SensorVoltage: INPUTS.O2SensorVoltage.default,
  ECT1Voltage: INPUTS.ECT1Voltage.default,
  ECT2Voltage: INPUTS.ECT2Voltage.default,
  AccessoryLoad: INPUTS.AccessoryLoad.default,
  IgnitionSwitch: INPUTS.IgnitionSwitch.default,
  StartAuthorisation: INPUTS.StartAuthorisation.default,
  StartRequest: INPUTS.StartRequest.default,
  StopRequest: INPUTS.StopRequest.default,
  EmergencyStop: INPUTS.EmergencyStop.default,
  ACRequest: INPUTS.ACRequest.default,
});
export const clip = (x: number, low: number, high: number): number => Math.min(Math.max(x, low), high);

// Call with a complete current snapshot. Omitted keys use initial defaults.
// The UI must merge an edited field into its current accepted input object first.
// Parse nonblank numeric text in the UI; reject invalid edits and keep the last value.
export function acceptInputs(raw: RawInputs = DEFAULT_INPUTS): { inputs: EngineInputs; clampedFields: Record<InputKey, boolean> } {
  const inputs = {} as EngineInputs, clampedFields = {} as Record<InputKey, boolean>;
  for (const key of Object.keys(INPUTS) as InputKey[]) {
    const def = INPUTS[key];
    let value = raw[key] === undefined ? def.default : raw[key];
    if (def.unit === '0/1' && typeof value === 'boolean') value = Number(value);
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      throw new TypeError(`${key} must be one finite number.`);
    }
    inputs[key] = clip(value, def.min, def.max);
    clampedFields[key] = inputs[key] !== value;
  }
  return { inputs, clampedFields };
}

export function ectTemperature(voltage: number): number {
  const v = clip(voltage, 0.2, 4.8);
  let t;
  if (v >= 4.3) t = -20 + (4.8 - v) * 40;
  else if (v >= 3.5) t = (4.3 - v) * 31.25;
  else if (v >= 2.5) t = 25 + (3.5 - v) * 25;
  else if (v >= 1.5) t = 50 + (2.5 - v) * 25;
  else if (v >= 1.0) t = 75 + (1.5 - v) * 30;
  else if (v >= 0.6) t = 90 + (1.0 - v) * 37.5;
  else if (v >= 0.3) t = 105 + (0.6 - v) * (20 / 0.3);
  else t = 125 + (0.3 - v) * 100;
  return clip(t, -20, 135);
}

export function initialState(): InternalState {
  return { engineState: STATES.OFF, elapsedInState: 0, sampleIndex: -1 };
}
const safeStart = (u: Readonly<EngineInputs>): boolean => u.IgnitionSwitch > 0.5 && u.StartAuthorisation > 0.5 &&
  u.StartRequest > 0.5 && u.EmergencyStop <= 0.5 && u.BatteryVoltage >= 9.5;

export function advanceState(u: Readonly<EngineInputs>, previous: Readonly<InternalState>): InternalState {
  const state = previous.engineState;
  let next = state, elapsed = previous.elapsedInState + DT;
  const abort = u.EmergencyStop > 0.5 || u.StopRequest > 0.5 || u.IgnitionSwitch <= 0.5;
  switch (state) {
    case STATES.OFF:
      if (safeStart(u)) next = STATES.PRIME;
      break;
    case STATES.PRIME:
      if (abort) next = STATES.SHUTDOWN;
      else if (elapsed >= 2.0) next = STATES.CRANK;
      break;
    case STATES.CRANK:
      if (abort || u.BatteryVoltage < 8.5) next = STATES.SHUTDOWN;
      else if (u.EngineSpeed >= 500) next = STATES.RUN;
      else if (elapsed >= 5.0) next = STATES.SHUTDOWN;
      break;
    case STATES.RUN:
      if (abort) next = STATES.SHUTDOWN;
      break;
    case STATES.SHUTDOWN:
      if (elapsed >= 0.5) next = STATES.OFF;
      break;
    default: throw new RangeError('Unknown internal engine state');
  }
  if (next !== state) elapsed = 0;
  return { engineState: next, elapsedInState: elapsed, sampleIndex: previous.sampleIndex + 1 };
}

// Pure algebra for one accepted input snapshot and one already-updated state.
export function calculateOutputs(u: Readonly<EngineInputs>, s: Readonly<InternalState>): EngineOutputs {
  const state = s.engineState;
  const FuelPumpState = Number(state === 1 || state === 2 || state === 3);
  const StarterState = Number(state === 2);
  const InjectionEnable = Number(state === 2 || state === 3);
  const IgnitionEnable = InjectionEnable;
  const ECT1Temp = ectTemperature(u.ECT1Voltage);
  const ECT2Temp = ectTemperature(u.ECT2Voltage);
  const EngineLoad = clip(0.55 * ((u.ManifoldPressure - 20) / 85) * 100 +
    0.45 * u.ThrottlePosition, 0, 100);
  const LambdaEstimate = clip(1 + (0.45 - u.O2SensorVoltage) * 0.35, 0.75, 1.25);
  const ClosedLoopActive = Number(InjectionEnable > 0.5 && ECT1Temp >= 70 && u.EngineSpeed >= 600);
  const STFT = ClosedLoopActive ? clip((LambdaEstimate - 1) * 120, -25, 25) : 0;
  const WarmupEnrichment = clip((70 - ECT1Temp) * 0.5, 0, 40);
  const BatteryCompensation = clip((13.8 - u.BatteryVoltage) * 0.18, 0, 1.2);
  const BaseInjectorPW = clip(1 + 0.00035 * u.EngineSpeed +
    0.025 * (u.ManifoldPressure - 20) + 0.012 * u.ThrottlePosition, 1, 15);
  const InjectorPW = InjectionEnable ? clip((BaseInjectorPW + BatteryCompensation) *
    (1 + (STFT + WarmupEnrichment) / 100), 0, 20) : 0;

  const ActualRPM = u.EngineSpeed;
  const TargetIdleRPM = 750 + clip((80 - ECT1Temp) * 5.625, 0, 450);
  const IdleActive = Number(state === 3 && u.ThrottlePosition <= 5 && u.EngineSpeed < 2000);
  const RPMError = IdleActive ? TargetIdleRPM - ActualRPM : 0;
  const IdleControlDuty = IdleActive ? clip(25 + 0.06 * RPMError + 0.25 * u.AccessoryLoad, 0, 100) : 0;
  const IgnitionTiming = !IgnitionEnable ? 0 : state === 2 ? 5 : clip(
    10 + 0.004 * (u.EngineSpeed - 800) - 0.08 * (u.ManifoldPressure - 35) + 0.015 * RPMError, -5, 45);

  const SensorDifference = Math.abs(ECT1Temp - ECT2Temp);
  const SensorDisagreement = Number(SensorDifference > 15);
  const ControlTemperature = Math.max(ECT1Temp, ECT2Temp);
  const T = ControlTemperature;
  let FanDuty = 0, WaterPumpDuty = 0;
  if (u.EmergencyStop > 0.5 || u.BatteryVoltage < 8) {
    FanDuty = 0; WaterPumpDuty = 0;
  } else if (SensorDisagreement) {
    FanDuty = 100; WaterPumpDuty = 100;
  } else {
    if (T < 88) FanDuty = 0;
    else if (T < 95) FanDuty = 20 + (T - 88) * (30 / 7);
    else if (T < 105) FanDuty = 50 + (T - 95) * 5;
    else FanDuty = 100;
    // Preserve state>=2, including SHUTDOWN=4.
    if (u.ACRequest > 0.5 && state >= 2) FanDuty = Math.max(FanDuty, 35);
    if (state === 3) {
      if (T < 50) WaterPumpDuty = 35;
      else if (T < 90) WaterPumpDuty = 35 + (T - 50) * (35 / 40);
      else if (T < 110) WaterPumpDuty = 70 + (T - 90) * 1.5;
      else WaterPumpDuty = 100;
    } else if (T > 95) WaterPumpDuty = 60;
  }
  FanDuty = clip(FanDuty, 0, 100);
  WaterPumpDuty = clip(WaterPumpDuty, 0, 100);
  return {
    EngineState: state, EngineStateLabel: STATE_NAMES[state], StateElapsedTime: s.elapsedInState,
    FuelPumpState, StarterState, InjectionEnable, IgnitionEnable,
    StartPermitted: FuelPumpState, SafeStartCondition: Number(safeStart(u)),
    InjectorPW, STFT, LambdaEstimate, ClosedLoopActive, EngineLoad, BaseInjectorPW,
    WarmupEnrichment, BatteryCompensation,
    ActualRPM, TargetIdleRPM, RPMError, IdleControlDuty, IgnitionTiming, IdleActive,
    ECT1Temp, ECT2Temp, FanDuty, WaterPumpDuty, SensorDifference, ControlTemperature,
    SensorDisagreement, CoolingLoopActive: Number(FanDuty > 0 || WaterPumpDuty > 0),
  };
}

// Exactly ONE discrete transition/update. No wall-clock time enters the equations.
// First invocation records sampleIndex=0, timestamp=0, and increments state elapsed by DT.
export function stepEngineModel(rawInputs: RawInputs, previous: Readonly<InternalState> = initialState()): ModelSnapshot {
  const { inputs, clampedFields } = acceptInputs(rawInputs);
  const internalState = advanceState(inputs, previous);
  return { inputs, clampedFields, internalState,
    simulationTime: internalState.sampleIndex * DT,
    outputs: calculateOutputs(inputs, internalState) };
}

// Initial/reset preview only; it does NOT advance state or create a history sample.
export function previewEngineModel(rawInputs: RawInputs = DEFAULT_INPUTS, internalState: Readonly<InternalState> = initialState()): ModelSnapshot {
  const { inputs, clampedFields } = acceptInputs(rawInputs);
  return { inputs, clampedFields, internalState,
    simulationTime: Math.max(0, internalState.sampleIndex) * DT,
    outputs: calculateOutputs(inputs, internalState) };
}

```

### JSON compatible integration contract

The TypeScript block defines EngineInputs, InternalState, EngineOutputs and
ModelSnapshot. Retain these field names at the module boundary, or provide one
explicit host adapter; do not let display labels become API identifiers.
ModelSnapshot contains inputs (the accepted values), clampedFields, internalState,
simulationTime in seconds, and outputs (30 numeric signals plus EngineStateLabel).
Use plain serializable objects and finite values; no DOM elements, classes,
functions, dates, maps or framework stores inside the numerical data contract.

`initialState()` creates OFF with elapsed 0 and sampleIndex -1.
`stepEngineModel(fullInputs, previousState)` advances exactly one sample and
returns a new snapshot. Save `snapshot.internalState` for the next call.
`previewEngineModel(fullInputs)` provides an unrecorded initial/reset display.
Input errors are rejected before advancing state. The UI must retain the last
accepted snapshot and show the field error; it must not crash or reset the model.

Example complete input message:

```json
{
  "BatteryVoltage": 13.8, "EngineSpeed": 800, "ThrottlePosition": 2,
  "ManifoldPressure": 35, "O2SensorVoltage": 0.45,
  "ECT1Voltage": 1.0, "ECT2Voltage": 1.1, "AccessoryLoad": 10,
  "IgnitionSwitch": 1, "StartAuthorisation": 1, "StartRequest": 1,
  "StopRequest": 0, "EmergencyStop": 0, "ACRequest": 0
}
```

This example requests start; it does not set RUN directly. At warm RUN the key
outputs are InjectorPW 1.679 ms, STFT 0%, TargetIdleRPM 750 rpm, IdleControlDuty
24.5%, IgnitionTiming 9.25 degrees BTDC, FanDuty 28.57142857142857% and
WaterPumpDuty 70%. Preserve all other output fields too.

### Active condition explanations

Show which condition controls the current response, using the same snapshot:
input capped; closed loop active/inactive and why; positive/negative fuel trim;
warm-up enrichment; idle inactive because of state, TPS or RPM; fixed crank
timing; cooling disagreement; A/C fan minimum; non-RUN hot pump; emergency
override; and the actual cause of a blocked start or state transition.
Respect branch priority. For example, emergency suppresses both cooling commands
even if ECT disagreement is present. StartPermitted means sequence active, while
SafeStartCondition includes the momentary start request. Do not create fake
diagnostic trouble codes or label a released start pulse as a running fault.

## 5 State sequence and details that must remain intact

State codes: 0 OFF -> 1 PRIME -> 2 CRANK -> 3 RUN -> 4 SHUTDOWN -> 0 OFF.
Only one transition is evaluated per sample; reset state elapsed on transition.

OFF: safe-start requires ignition, authorisation, start request, no emergency
and battery >=9.5 V. When true enter PRIME. StopRequest is not in this predicate.
PRIME: emergency, stop or ignition-off -> SHUTDOWN; otherwise after >=2 s -> CRANK.
CRANK: emergency, stop, ignition-off or battery <8.5 -> SHUTDOWN; otherwise
RPM >=500 -> RUN; otherwise after >=5 s -> SHUTDOWN. The RPM branch precedes timeout.
RUN: emergency, stop or ignition-off -> SHUTDOWN. No automatic stall, low-RPM
shutdown, low-battery shutdown or authorisation-loss shutdown exists in RUN.
SHUTDOWN: after >=0.5 s -> OFF.

Fuel pump is ON in PRIME/CRANK/RUN; starter only in CRANK; injection and ignition
are enabled in CRANK/RUN. StartPermitted is the existing name of the active
sequence indicator (same as FuelPumpState), not a live check that start is safe.
Label it "Sequence active" in the UI. SafeStartCondition includes StartRequest;
it naturally returns false after a momentary start pulse even if the engine is
already RUN. Do not label this as a running-engine fault.

Preserve these model behaviours even where a real ECU might behave differently:
  - Holding StartRequest high can start another sequence after SHUTDOWN/OFF.
  - OFF with StopRequest and a safe start can enter PRIME for one sample.
    The ordinary Start button clears StopRequest and is only offered in OFF.
  - Closed loop requires injection enabled, ECT1 >=70 deg C and RPM >=600.
  - Idle active requires RUN, TPS <=5% and RPM <2000. RPMError is zero outside
    idle mode; do not use an unconditional RPM difference in ignition timing.
  - Sensor disagreement is strictly >15 deg C, not >=15.
  - Emergency has priority over cooling disagreement and commands both duties 0.
  - Cooling has no blanket ignition/run enable: a warm fan can run while OFF.
  - Outside RUN, pump duty is 60% only when control temperature >95 deg C,
    unless disagreement forces 100% or emergency forces 0%.
  - A/C's fan minimum applies when state code >=2, including SHUTDOWN=4.
  - The <8 V cooling cut-off is unreachable after the 8 V input cap. Keep it in
    the translated logic; do not bypass the cap to make it reachable.
  - Some output clamps are not reachable with permitted inputs. Preserve both
    input caps and output clamps instead of widening inputs to reach them.
Explain unusual results with short contextual text. Change the engineering
behaviour only after a separate explicit instruction to revise the model.

## 6 Simulation controls and lifecycle

Clearly separate simulation time controls from engine operating requests:
  - Run simulation / Pause / Resume: control the 50 ms numerical loop.
  - Step 0.05 s: advance exactly one sample while paused.
  - Start engine: create StartRequest=1 for 10 model calls, then clear it.
    It does not set RUN directly. Clear StopRequest before this pulse.
  - Stop engine: clear any pending StartRequest; pulse StopRequest for 10 calls.
    It does not stop the simulation clock, so shutdown/cooling remain observable.
  - Emergency stop: latch EmergencyStop=1 until an explicit Clear emergency
    action or a clearly labelled Reset all. Clearing it never starts the engine.
  - Reset all: pause, cancel pulses, restore input defaults, state OFF/time zero,
    clear event/trend history and create an unrecorded initial preview.

Start/stop pulses count model calls, not wall-clock time or screen frames.
Disable ordinary Start/Stop engine actions while paused and explain "Run or
resume the simulation first". Permit input edits and single-step experiments.
Paused readouts/history remain the last sampled snapshot. Mark edited controls
as pending until Step/Resume; never show new inputs beside old outputs without
this distinction. Emergency edits made while paused are also visibly pending
until Step/Resume. This is a virtual experiment, with no hardware connection.
The initial preview may display algebraic cooling commands while the model is
OFF; label it "Ready - simulation paused" and do not animate it.

Use one owner for model state and one scheduler. At normal speed accumulate
wall-clock time and execute fixed 0.05 s steps; animation frames may interpolate
presentation only. Never use a variable frame delta as the numerical dt.
Pause automatically when the section is hidden/inactive or the browser tab is
hidden; resume deliberately with a fresh wall-clock anchor. Avoid a long burst
of catch-up samples after inactivity. On a long scheduler stall, pause with a
brief message instead of jumping across seconds of unseen model history.
Clean up timers/listeners on unmount and avoid duplicate loops after remount.
Re-rendering, opening a subpanel and changing an input must not reset state/time.

Provide a visible event list for state changes and blocked start attempts,
including the simulation timestamp and a reason. Derive reasons from actual
inputs/conditions; do not invent a diagnostic fault-code system.

## 7 Required student interface and graphical result

Deliver a complete usable section, not just a calculation library, proposal,
code snippets or decorative car picture. Use the existing platform's design.

Desktop composition, adapted to the host layout:
  Top: Engine Live-Data Demonstration title, simulation status/time, controls,
       preset selector and a clear OFF/PRIME/CRANK/RUN/SHUTDOWN sequence strip.
  Left: compact grouped sensor controls and operating switches.
  Centre: interactive stationary engine-system cutaway/schematic with callouts.
  Right: key numerical output cards and current cause-and-effect explanation.
  Below: Overview and four detail panels (Fuel & Injection; Idle & Ignition;
         Cooling; Start/Run), live trends, legends and event history.
On narrow screens stack these areas in a readable order with usable touch targets.
Do not force the host site into a new overall layout or visual identity.

REQUIRED GRAPHIC: a clear 2D SVG (or equivalent host-native vector) engine-system
illustration with battery, authorisation/ECU, starter, fuel pump/injector, ignition,
engine/RPM, two ECT callouts, radiator/fan and a labelled VIRTUAL electric pump.
Use a compact "signal/control" legend distinct from "illustrative flow/motion".
Place ECT1/ECT2 as virtual signal callouts; do not claim unmodelled inlet/outlet
sensor positions or infer a coolant gradient from their placement.

A stationary car silhouette can provide context, with the engine compartment
highlighted. A moving or road-driving car is not required or appropriate for
this model, which has no vehicle-speed/road model. Do not add heavy 3D or paid
assets when a clean vector cutaway can explain the relationships more clearly.
An existing lightweight 3D engine viewer may be reused, provided every command
and label still follows the same snapshot and a readable 2D/text fallback exists.

Bind graphics as follows:
  - Battery: accepted voltage label and state-appropriate start-condition cue.
  - Authorisation: simulated authorised/not-authorised icon with text.
  - Fuel pump: ON/OFF from FuelPumpState, including PRIME before injection.
  - Injector: InjectionEnable gates activity; numeric pulse width uses InjectorPW.
    A bounded bar/pulse may illustrate width; no claim of crank-synchronised
    injection frequency, fuel mass, cylinder phasing or combustion accuracy.
  - Ignition: enabled lamp + timing indicator from IgnitionEnable/IgnitionTiming.
    Zero timing with disabled ignition must be labelled disabled, not a live spark.
  - Starter: active only when StarterState=1; label the starter command separately
    from measured/imposed engine motion.
  - Engine rotation: an illustrative RPM indicator only when state is CRANK/RUN
    AND imposed RPM >0. Use a bounded monotonic speed mapping and label it
    illustrative. Do not rotate merely because RUN is true when RPM is zero.
    An OFF state with RPM input still 800 is possible: show the input faithfully
    and explain that it is imposed, without faking an operating engine.
  - Fan: rotation/duty bar from FanDuty, including OFF/SHUTDOWN cooling behaviour.
  - Virtual pump: rotation/duty bar from WaterPumpDuty. Illustrative coolant-flow
    markers follow this duty, not engine state. No litres/min, pressure or thermal
    transport claim. A temperature colour must reflect accepted converted ECTs.
  - ECT disagreement: show both values, difference, >15 deg C status and actual
    resulting commands. Under emergency, explain suppression of the 100% response.
  - Sequence: highlight the actual EngineState; relay/enable lamps use exact flags.

Graphics may exaggerate motion for visibility, with a persistent short label
"Illustrative motion - values come from the model". Duty percentage is a command,
not a measured fan/pump speed. Motion freezes during Pause and respects reduced
motion preferences. Static labels/bars must communicate everything without motion.
Keep animations restrained and avoid rapid flashing. Do not make colour alone
convey state. Keyboard access, visible focus, readable contrast and chart/data
alternatives are required. Clicking a component should reveal its inputs,
calculation, current outputs and a short plain-language explanation.

## 8 Outputs, graphs, units and legends

Use four understandable categories: imposed sensor inputs; calculated values;
actuator commands; operating states. Keep all 30 numerical/boolean model outputs
available in detail panels. EngineStateLabel is the text rendering of EngineState.

Start/Run (8): EngineState [code + label], StateElapsedTime [s], FuelPumpState,
StarterState, InjectionEnable, IgnitionEnable, StartPermitted, SafeStartCondition
[last six 0/1 with readable status labels].
Fuel (8): InjectorPW [ms], STFT [%], LambdaEstimate [ratio], ClosedLoopActive [0/1],
EngineLoad [%], BaseInjectorPW [ms], WarmupEnrichment [%], BatteryCompensation [ms].
Idle/Ignition (6): ActualRPM [rpm], TargetIdleRPM [rpm], RPMError [rpm],
IdleControlDuty [%], IgnitionTiming [deg BTDC; negative means ATDC], IdleActive [0/1].
Cooling (8): ECT1Temp, ECT2Temp [deg C], FanDuty, WaterPumpDuty [%],
SensorDifference, ControlTemperature [deg C], SensorDisagreement, CoolingLoopActive [0/1].

Every graph/scope MUST have a visible legend naming every trace, units on each
vertical axis, simulation seconds on the horizontal axis, labelled values on
hover/focus, and distinguishable line styles/colours. Use separate aligned panels
for different units; do not plot RPM, milliseconds and temperature on one axis.
Use step traces for states/binaries with a visible 0/1 or state-code legend.
At least provide these default trend groups, plus a signal selector for the rest:
  Fuel: O2 voltage; lambda; STFT; injector pulse width (separate unit panels).
  Idle: actual and target RPM together; RPM error; idle duty; ignition timing.
  Cooling: ECT1, ECT2 and control temperature together; fan and pump duty together;
           sensor difference with the 15 deg C threshold clearly identified.
  Start/Run: state with OFF/PRIME/CRANK/RUN/SHUTDOWN key; relay/enable step traces.
Store a bounded rolling 60-second history (up to 1201 samples at 0.05 s); keep
it visible while paused. Preserve time alignment when decimating for rendering.
Give students a readable table or accessible alternative to the charts.

Provide CSV export for the retained sampled window, not invented full-session
data. One row per model sample: simulation_time_s; all 14 accepted inputs; all 30
outputs; EngineStateLabel. Include units in headers or an in-app field key.
Export inputs and outputs from their historical snapshots, not current controls.
Disable export before any sample exists and explain why. Do not export passwords,
identity data or physical rig records; these are not part of this section.

## 9 Presets and manual experiments

Provide a small preset selector. A preset loads the listed eight numeric inputs
using the defaults for unspecified fields, resets state/history and pauses ready
for a new experiment. Reset normal binary flags to 0; set A/C as listed. Preserve
a latched EmergencyStop until deliberately cleared or Reset all is selected.
Tell the student that selecting a preset starts a fresh experiment.
Presets never silently force RUN or invent sensor feedback.

Warm idle: all numeric defaults, A/C=0.
Lean signal: O2=0.10 V; otherwise warm idle.
Rich signal: O2=0.90 V; otherwise warm idle.
Idle load disturbance: battery=13 V, RPM=620, MAP=45 kPa, accessory load=80%, A/C=1.
Hot cooling: RPM=900, TPS=3%, MAP=38 kPa, ECT1=0.55 V, ECT2=0.62 V,
             accessory load=20%, A/C=1.
ECT disagreement: ECT1=1.0 V, ECT2=2.0 V; otherwise warm idle.
Low battery: battery=9.0 V; otherwise warm idle.
Cold engine signals: ECT1=3.5 V, ECT2=3.5 V; otherwise warm idle.
Slow cranking: RPM=200; otherwise warm idle.

General student sequence: select preset -> Run simulation -> enable Ignition
and Simulated authorisation -> Start engine -> observe the sequence -> change
one parameter -> read its resulting values, explanation and trends -> Pause
or Step -> export if useful. Stop engine demonstrates shutdown; Pause stops time.
A visible "Try this" card should suggest one change and what relationship to
observe, without claiming measured physical outcomes.

## 10 Numerical and interaction acceptance

Use the following manual checks and the embedded core as the implementation
oracle. Do verification within the existing repository's normal workflow;
do not hand the user a separate collection of test scripts or model files.
Keep full precision for checks (absolute tolerance 1e-9 for listed continuous
values); compare booleans and state codes exactly. Display rounding is separate.
Approximate figures below are rounded for readability; use the stated precision
or exact embedded formula where appropriate.

For warm-idle numerical values, set numeric defaults, ignition/auth/start=1 and
other flags=0, reset core, then evaluate t=0 through t=3 inclusive (61 calls).
UI momentary start produces the same RUN steady outputs, except SafeStartCondition
is 0 once the pulse is released. Reference held-start checks have it equal to 1.

Scenario / expected values
Warm RUN: state=3; injector=1.679 ms; lambda=1; STFT=0%; load=10.605882352941178%;
target=750 rpm; actual=800; error=-50; idle duty=24.5%; timing=9.25 deg BTDC;
ECT1=90 deg C; ECT2=87; fan=28.57142857142857%; pump=70%; closed loop=1.
Lean, O2=0.10: lambda=1.1225; STFT=14.7%; injector=1.925813 ms.
Rich, O2=0.90: lambda=0.8425; STFT=-18.9%; injector=1.361669 ms.
Idle disturbance preset in RUN: error=130 rpm; duty=52.8%; timing=10.43 deg BTDC;
injector=2.010 ms; fan=35%; pump=70%.
Hot cooling preset in RUN: ECT1=108.33333333333333 deg C; ECT2=104.25;
fan=100%; virtual pump=97.5%.
ECT disagreement preset: temperatures=90 and 62.5 deg C; difference=27.5;
disagreement=1; fan=pump=100%, unless emergency is active.
Battery=9 V with start requested: remains OFF; fuel pump/starter/injection/ignition
disabled; InjectorPW=0. Do not require fan=0: warm default signals command a fan.
Cold signals in RUN: both temperatures approximately 25 deg C; closed loop=0;
STFT=0; enrichment=22.5%; injector=2.056775 ms; target=1059.375 rpm;
error=259.375; idle duty=43.0625%; timing=13.890625; fan=0%; pump=35%.
Slow crank: RPM=200 with held ignition/auth/start; sample t=7.4 (149 calls)
is SHUTDOWN, elapsed=0.35 s, enables=0. Held start can later retrigger; do not
mistake this for a failure of the timeout. The ordinary start pulse avoids it.
Caps: battery16->14.9; RPM-100->0; TPS120->100; MAP10->20; O2 1.2->0.95;
ECT1 0.1->0.2 (135 deg C). Check every input's minimum and maximum.
Emergency active from OFF: stays OFF; all relay/enables=0; fan=pump=0.

Also verify these interactions in the integrated UI:
  - Start remains blocked without ignition/authorisation, with battery <9.5 V,
    or with EmergencyStop=1, and the reason is understandable.
  - CRANK exits to RUN at RPM>=500; idle mode is gated by TPS/RPM exactly.
  - From RUN, change O2 from 0.45 to 0.10 without resetting state/time: injector
    changes from 1.679 to 1.925813 ms. Graph and graphic agree with the same sample.
  - Stop/ignition-off/emergency transition correctly; E-stop in RUN disables
    relay/enables and both cooling commands on the next processed sample.
  - ECT1=ECT2=0.6 V while OFF yields temperature105, fan100 and pump60;
    fan/pump visual motion must not be gated by RUN. Under emergency both become0.
  - Exactly 15 deg C disagreement does not trigger the >15 response.
    Example ECT1=1.0 V (90 deg C), ECT2=1.5 V (75 deg C).
  - RUN with RPM subsequently set to0 stays RUN per this model, while imposed
    engine-rotation animation stops. Explain rather than changing the logic.
  - A/C in SHUTDOWN can impose the 35% fan minimum; emergency overrides it.
  - Pausing freezes time, pulses, history and motion. Resume has no clock jump.
  - Reset works; presets do not clear an E-stop latch implicitly; input changes,
    resize and switching detail panels do not create duplicate loops/state resets.
  - All scopes have legends/units; every output is accessible; CSV matches samples.
  - The host navigation works, the section is usable on a narrow screen, keyboard
    operation works, and reduced motion loses no numerical/status information.

## 11 Done means an integrated, visible result

Implement the translated core, its fixed-step controller and the polished
student interface in the existing application. Verify the numerical checks,
run the appropriate host build/checks and inspect the rendered section in the
available browser/UI tooling. Fix layout, interaction and numerical issues.
Use repository conventions for any internal checks; keep the user-facing
handover simple. Do not create a second prototype instead of integration.

The final report to the platform owner must include:
  1. The changed files, run instructions, and route/navigation location where the section can be opened.
  2. A concise description of the completed controls and four model panels.
  3. A screenshot or available live preview showing the corresponding graphical
     output, real model values, the state strip, and visible trend legends.
  4. Verification actually performed and any remaining limitations or blockers.

Do not claim the work complete with only logic and no corresponding visual
output, or only graphics and no functioning model. Do not report a visual check
that was not performed. If the environment prevents it, identify that limitation.
Keep the permanent user-facing explanation short: these are educational virtual
signals and commands; the physical 1NZ stage is separate and has no electric pump.

## End of implementation instructions
