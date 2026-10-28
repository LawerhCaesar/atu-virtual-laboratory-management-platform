# Codex battery energy management implementation script

Read this file as the complete task instruction for implementing the battery
energy management module in the existing virtual platform. The companion
`PROGRAMMER_GUIDE.docx` explains the expected product for the programmer.

This is a self-contained Markdown handoff. The final section embeds the tested
JavaScript engine, native MATLAB fixtures and executable checks. Before running
the Node commands below, extract the single `javascript` code block between
`BEGIN_EXECUTABLE_ENGINE` and `END_EXECUTABLE_ENGINE` into
`battery-platform-kit.mjs` in the implementation workspace. Copy the code
verbatim, omitting the Markdown fences and marker comments. The JavaScript file
is generated from this script; it is not an additional handoff dependency.

Run `node battery-platform-kit.mjs --self-test` after extraction. Retain the
1-second timing, all 32 output channels, validation fixtures and documented
scope. Use the full implementation instructions below, then deliver the
required interactive visuals and platform integration.


## Task For Codex

Integrate the battery energy management concept into the user's virtual
platform as a working, approachable browser-based learning experience.
Use the executable engine in this file. It is already a JavaScript translation;
do not re-invent the equations or replace them with scripted demonstration data.
Inspect the platform repository, its instructions, navigation, design system,
test tools and runtime before choosing the integration location. Follow its
existing framework. Keep the engine independent of components and rendering.
If the repository requires another language, port these equations and exact
timing semantics, retain the same named output contract, and prove equivalence.
If no platform source is available, build an isolated runnable browser module
with a documented host adapter and state what integration still requires.


## Context And Source Priority

The corrected source is Battery_Energy_Management_Organised.slx in
F:/Scripts for codex/Mr. Bernard. Its SHA256 is in MODEL_INFO.
The Battery_Model_Validation_2026-10-25 folder contains the original repair
report, native MATLAB test harness, full default trace and scenario summaries.
This chat records the original failure and verified repair:
https://chatgpt.com/s/cx_6ade5ed910a081919e5f619b73939bab
The share is a public, immutable snapshot of the repair discussion; it may not
include later messages. The local chat ID is recorded in MODEL_INFO for an
authorized Codex session with access to that history. These identifiers are
context references, not runtime dependencies. Do not fetch the chat in the app.
If a link or F drive is unavailable, this file still supplies the implementation,
defaults, selected native reference rows, all 30 scenario endpoints and checks.
Compare any newer source version before changing these equations. If the SLX
is available but its hash differs, report the mismatch and reconcile the source.
Keep the repaired SLX unchanged while implementing the platform.


## Required Numerical Behavior

Use JavaScript Number (double precision), a fixed 1-second physics interval,
linear OCV interpolation and explicit state updates. The original repair sets
21 comparison outputs to Boolean and combines two thermal predicates with
logical AND. Preserve comparisons and short-circuit logic, not Boolean
multiplication or truthy string values. Negative current charges, positive
current supplies a load, and zero is rest. Ambient and initial pack temperature
are distinct inputs. Ns changes voltage; Np changes capacity and resistance.

Observe outputs from the state at time t; then advance the state by one second.
At t = stepTimeS, the new request is already active. A 3600-second run includes
3601 output rows, t=0 through t=3600, and exactly 3600 state advances. The
energy/charge totals at t=0 are zero. Do not add the t=3600 current for another
second. Preserve status tolerance 1e-8 A and efficiency tolerance 1e-9 W.
Use nominal energy only for available-energy and headroom estimates.
Electrical efficiency is separate from coulombic efficiency. Raw efficiency
-1 means not applicable; show an em dash or N/A, never -100%, in the UI.
Charging power magnitude, discharging power and ohmic loss are nonnegative;
terminal power is signed. The temperature state is one pack average.
The engine must remain deterministic and must not depend on animation FPS.


## Integration Contract

Use createBatteryModel(overrides) to validate and freeze a parameter set.
initialState() returns an independent JSON-serializable state.
observe(state, {requestedCurrentA, ambientC}) returns the 32 named channels,
Time_s, and additional limiter diagnostics. It never changes the state.
step(state,input) returns {output,nextState}; output is the pre-update sample.
Use observe at a final boundary without an extra step. runScenario implements
this convention. outputToRow and rowsToCsv preserve the MATLAB column order.
Keep UI-friendly labels in deriveViewModel; preserve raw values for export.
Use one authoritative state instance per simulation. Reset replaces it.
Host applications own start, pause, resume, reset, playback, persistence and
navigation. Clean up timers/workers/listeners when the module is removed.
Never duplicate physics calculations in an SVG, chart component or adapter.
Use a worker or bounded chunks for long batch runs to keep controls responsive.
For a live mode, queue current and ambient changes for the next integer time
boundary and record the applied time. Parameter/initial-condition changes
create a new run. Do not mutate an existing run's historical configuration.


## Required User Experience

Create an opening state ready to run the default charge-then-discharge case.
Provide Run, Pause/Resume, Reset, and Step 1 second, plus simulation time,
duration and playback speed (1x, 10x, 60x). Faster playback executes more fixed
steps per wall-clock interval; it never enlarges the physics timestep.
Default behavior when the tab becomes hidden is pause with a visible notice.
Use the animation timestamp and a fixed-step accumulator; use render
interpolation only for motion, never to integrate battery state. Cap work per
frame and preserve pending physics steps; do not silently skip simulated time.
Optional completed-run playback/scrubbing displays recorded samples and must
not integrate state a second time or change the exported data.

Put basic controls first: a mode selector (charge, supply load, rest, profile),
current magnitude in A, ambient temperature in degC, initial SOC, initial pack
temperature, duration, and profile step time. Convert charge magnitude to a
negative signed request at the adapter boundary. Include editable numeric
fields with sliders, units, valid ranges and inline validation. Never silently
clamp user settings or pass empty input as zero. Disable Run while invalid.
An Advanced settings panel exposes every DEFAULT_PARAMETERS field, describes
the array ordering, shows pack totals, and supports reset to baseline.
Offer named teaching presets for normal cycling, high-current limiting,
near-full/near-empty SOC, cold/hot blocked operation, thermal derating and
voltage limiting. Exclude the extreme one-step guard test from normal presets.


## Mandatory Corresponding Visual Output

Deliver a responsive scene of a car silhouette/cutaway with an identifiable
battery pack, charger/source, electrical load and paths for energy flow.
Use editable SVG or native platform drawing as the baseline implementation.
It must show data-driven animation, not a static hero image or prerecorded
video. A 3D car is optional polish if the host already supports it; the
mathematics does not require 3D. Do not add a heavy 3D stack solely for this.

Bind every visual to the current engine sample:
1. Battery fill uses SOC_pct on a true 0-100% scale with 5% and 95% baseline
   limit markers. Show the exact percentage and the configured thresholds.
2. Charging: particles/arrows travel source -> battery when Actual_A < -1e-8.
   Supply: particles/arrows travel battery -> load when Actual_A > 1e-8.
   Rest or blocked: no solid flow. Requested-but-rejected flow may appear as a
   clearly labeled dashed intent path, separate from permitted flow.
3. Show requested and allowed A side by side, signed terminal kW, and rejected
   current magnitude. Arrow intensity can use absolute terminal power with a
   documented visual cap. Never interpret that cap as a physical limit.
4. The temperature color/thermometer uses Temperature_C and active-direction
   thresholds; label it Average pack temperature. Show Loss_W as a numerical
   heat-loss readout, optionally a subtle heat effect. Do not depict measured
   individual-cell hotspots or thermal runaway that this model does not compute.
5. Display the operating state and primary limiting reason in plain language
   with text/icon as well as color. Show the requested/allowed difference and
   which candidate limits are binding. Multiple constraints may apply; the
   primary code must retain the engine's original tie precedence.
6. Show Ns x Np and pack V/Ah/kWh in an information view. Any drawn cells are
   representative; the model is a balanced equivalent pack, not individual
   cell simulations. Car movement, wheel RPM, speed, acceleration, road grade
   and driving range are not computed here. Do not fabricate these outputs.
   A stationary car with truthful energy-flow animation is the default.

Build eight chart groups, sharing the same time axis and cursor: SOC;
pack/ambient temperature; requested/allowed current; OCV/terminal voltage;
signed terminal power/ohmic loss; energy received/supplied/lost; nominal
available-energy/headroom estimates; charge/discharge current limits.
Use units, legends and readable tooltips, with markers at profile changes and
state/limiter transitions. Preserve signed values on axes. Provide an event
list for state/reason transitions and a table exposing all 32 channels.
Show efficiency (when applicable), charged/discharged Ah and power-balance
residual in an expandable results area. Export raw CSV with full precision and
a separate JSON run configuration containing version, parameters, inputs,
applied input events, fixed timestep and duration. Never export rounded UI text.
Downsample only chart rendering; keep complete simulation/export data.

Desktop: prominent scene and concise readouts, an adjacent controls panel, and
charts below. Small screens: stack these without clipping labels or controls.
Include keyboard operation, visible focus, accessible names, non-color status
cues and a reduced-motion mode that preserves arrows, labels and all data.
Avoid flashes. Honor prefers-reduced-motion. Do not announce every sample to
assistive technology; announce meaningful status changes and user actions.
Show one concise product note that parameters are illustrative and the output
is a learning simulation. Keep developer details out of the main learner view.


## Acceptance Gates And Required Delivery

1. Run this file's self-tests before integration and after any engine changes.
   Its embedded tests compare 30 scenario endpoints with native MATLAB results,
   verify selected 32-channel native default samples, and check invariants over
   63,398 sample rows. Seven native invalid settings plus API hardening cases
   must reject cleanly. All statuses 0-6 and reasons 0-4 must be covered.
2. If the native default CSV is accessible, run --compare-csv against it. Require
   all 3601 rows and all 32 channels to agree within 2e-7*(1+abs(reference));
   status/reason/time must agree exactly. Do not widen tolerances to hide errors.
   Other scenarios have embedded native endpoints, not full embedded traces.
   If changing equations or porting language, export full native scenario traces
   and compare every channel; do not describe endpoint tests as full trace parity.
3. Verify UI integration: default 50 -> 75 -> 25% at t=0/1800/3600; idle;
   charge/discharge blocked; all limiter reasons; independent concurrent runs;
   reset; pause/resume; 1x versus 60x identical traces; hidden-tab pause;
   invalid/empty input; edited configuration reset; export; mobile layout;
   reduced motion; and no duplicate timer/listener after unmount/remount.
4. Capture screenshots and a short preview of charging, supplying, derating and
   blocked behavior. Check energy-flow direction, fill, labels and plots against
   the SAME engine sample. Include actual numeric readings in those checks.
5. Deliver working source integrated with platform navigation, the runnable
   preview URL or local start command, numerical/UI test results, visual proof,
   a host-adapter description and any remaining gaps. The handoff kit itself is
   not a completed interface. Do not call the platform work complete until the
   interactive scene, controls, charts and exports are implemented and tested.
   If a host integration is blocked, deliver the runnable module and identify
   the exact missing host interface. Keep completion claims scoped to evidence.


## Reference Links For Implementation Details

https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame
https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion

## Embedded tested engine and validation fixtures

Extract the code below as `battery-platform-kit.mjs`. It is the previously
tested engine, unchanged. This block is complete and requires no packages.

<!-- BEGIN_EXECUTABLE_ENGINE -->
```javascript
/**
 * Battery energy management platform kit, version 1.0.0, 25 October 2026.
 * START HERE, CODEX: read CODEX_IMPLEMENTATION_BRIEF below, then the engine.
 * This single file contains the implementation contract, portable JavaScript
 * physics engine, MATLAB reference fixtures, and executable regression checks.
 * Import it as an ES module in a browser, worker, or Node. No packages required.
 * Node: node battery-platform-kit.mjs --self-test
 * Node: node battery-platform-kit.mjs --brief
 * Do not run this file as an operating-system shell script.
 */

export const MODEL_INFO = Object.freeze({
  version: '1.0.0',
  model: 'Battery_Energy_Management_Organised.slx',
  modelSha256: 'EB530DEEBA66EF27FE20C21EFB7E357D8D61A071467493291E07BCC1AB321931',
  sourceFolder: 'F:/Scripts for codex/Mr. Bernard',
  validationFolder: 'F:/Scripts for codex/Mr. Bernard/Battery_Model_Validation_2026-10-25',
  sharedChat: 'https://chatgpt.com/s/cx_6ade5ed910a081919e5f619b73939bab',
  localChatId: '01a1747b-4a0d-7e61-81da-6931315636c2',
  localChatTitle: 'Fix battery energy management model',
  sourceEnvironment: 'MATLAB R2024b / Simulink',
  stepSeconds: 1,
  use: 'Educational virtual battery simulation with illustrative calibration'
});

export const CODEX_IMPLEMENTATION_BRIEF = String.raw`
TASK FOR CODEX
Integrate the battery energy management concept into the user's virtual
platform as a working, approachable browser-based learning experience.
Use the executable engine in this file. It is already a JavaScript translation;
do not re-invent the equations or replace them with scripted demonstration data.
Inspect the platform repository, its instructions, navigation, design system,
test tools and runtime before choosing the integration location. Follow its
existing framework. Keep the engine independent of components and rendering.
If the repository requires another language, port these equations and exact
timing semantics, retain the same named output contract, and prove equivalence.
If no platform source is available, build an isolated runnable browser module
with a documented host adapter and state what integration still requires.

CONTEXT AND SOURCE PRIORITY
The corrected source is Battery_Energy_Management_Organised.slx in
F:/Scripts for codex/Mr. Bernard. Its SHA256 is in MODEL_INFO.
The Battery_Model_Validation_2026-10-25 folder contains the original repair
report, native MATLAB test harness, full default trace and scenario summaries.
This chat records the original failure and verified repair:
https://chatgpt.com/s/cx_6ade5ed910a081919e5f619b73939bab
The share is a public, immutable snapshot of the repair discussion; it may not
include later messages. The local chat ID is recorded in MODEL_INFO for an
authorized Codex session with access to that history. These identifiers are
context references, not runtime dependencies. Do not fetch the chat in the app.
If a link or F drive is unavailable, this file still supplies the implementation,
defaults, selected native reference rows, all 30 scenario endpoints and checks.
Compare any newer source version before changing these equations. If the SLX
is available but its hash differs, report the mismatch and reconcile the source.
Keep the repaired SLX unchanged while implementing the platform.

REQUIRED NUMERICAL BEHAVIOR
Use JavaScript Number (double precision), a fixed 1-second physics interval,
linear OCV interpolation and explicit state updates. The original repair sets
21 comparison outputs to Boolean and combines two thermal predicates with
logical AND. Preserve comparisons and short-circuit logic, not Boolean
multiplication or truthy string values. Negative current charges, positive
current supplies a load, and zero is rest. Ambient and initial pack temperature
are distinct inputs. Ns changes voltage; Np changes capacity and resistance.

Observe outputs from the state at time t; then advance the state by one second.
At t = stepTimeS, the new request is already active. A 3600-second run includes
3601 output rows, t=0 through t=3600, and exactly 3600 state advances. The
energy/charge totals at t=0 are zero. Do not add the t=3600 current for another
second. Preserve status tolerance 1e-8 A and efficiency tolerance 1e-9 W.
Use nominal energy only for available-energy and headroom estimates.
Electrical efficiency is separate from coulombic efficiency. Raw efficiency
-1 means not applicable; show an em dash or N/A, never -100%, in the UI.
Charging power magnitude, discharging power and ohmic loss are nonnegative;
terminal power is signed. The temperature state is one pack average.
The engine must remain deterministic and must not depend on animation FPS.

INTEGRATION CONTRACT
Use createBatteryModel(overrides) to validate and freeze a parameter set.
initialState() returns an independent JSON-serializable state.
observe(state, {requestedCurrentA, ambientC}) returns the 32 named channels,
Time_s, and additional limiter diagnostics. It never changes the state.
step(state,input) returns {output,nextState}; output is the pre-update sample.
Use observe at a final boundary without an extra step. runScenario implements
this convention. outputToRow and rowsToCsv preserve the MATLAB column order.
Keep UI-friendly labels in deriveViewModel; preserve raw values for export.
Use one authoritative state instance per simulation. Reset replaces it.
Host applications own start, pause, resume, reset, playback, persistence and
navigation. Clean up timers/workers/listeners when the module is removed.
Never duplicate physics calculations in an SVG, chart component or adapter.
Use a worker or bounded chunks for long batch runs to keep controls responsive.
For a live mode, queue current and ambient changes for the next integer time
boundary and record the applied time. Parameter/initial-condition changes
create a new run. Do not mutate an existing run's historical configuration.

REQUIRED USER EXPERIENCE
Create an opening state ready to run the default charge-then-discharge case.
Provide Run, Pause/Resume, Reset, and Step 1 second, plus simulation time,
duration and playback speed (1x, 10x, 60x). Faster playback executes more fixed
steps per wall-clock interval; it never enlarges the physics timestep.
Default behavior when the tab becomes hidden is pause with a visible notice.
Use the animation timestamp and a fixed-step accumulator; use render
interpolation only for motion, never to integrate battery state. Cap work per
frame and preserve pending physics steps; do not silently skip simulated time.
Optional completed-run playback/scrubbing displays recorded samples and must
not integrate state a second time or change the exported data.

Put basic controls first: a mode selector (charge, supply load, rest, profile),
current magnitude in A, ambient temperature in degC, initial SOC, initial pack
temperature, duration, and profile step time. Convert charge magnitude to a
negative signed request at the adapter boundary. Include editable numeric
fields with sliders, units, valid ranges and inline validation. Never silently
clamp user settings or pass empty input as zero. Disable Run while invalid.
An Advanced settings panel exposes every DEFAULT_PARAMETERS field, describes
the array ordering, shows pack totals, and supports reset to baseline.
Offer named teaching presets for normal cycling, high-current limiting,
near-full/near-empty SOC, cold/hot blocked operation, thermal derating and
voltage limiting. Exclude the extreme one-step guard test from normal presets.

MANDATORY CORRESPONDING VISUAL OUTPUT
Deliver a responsive scene of a car silhouette/cutaway with an identifiable
battery pack, charger/source, electrical load and paths for energy flow.
Use editable SVG or native platform drawing as the baseline implementation.
It must show data-driven animation, not a static hero image or prerecorded
video. A 3D car is optional polish if the host already supports it; the
mathematics does not require 3D. Do not add a heavy 3D stack solely for this.

Bind every visual to the current engine sample:
1. Battery fill uses SOC_pct on a true 0-100% scale with 5% and 95% baseline
   limit markers. Show the exact percentage and the configured thresholds.
2. Charging: particles/arrows travel source -> battery when Actual_A < -1e-8.
   Supply: particles/arrows travel battery -> load when Actual_A > 1e-8.
   Rest or blocked: no solid flow. Requested-but-rejected flow may appear as a
   clearly labeled dashed intent path, separate from permitted flow.
3. Show requested and allowed A side by side, signed terminal kW, and rejected
   current magnitude. Arrow intensity can use absolute terminal power with a
   documented visual cap. Never interpret that cap as a physical limit.
4. The temperature color/thermometer uses Temperature_C and active-direction
   thresholds; label it Average pack temperature. Show Loss_W as a numerical
   heat-loss readout, optionally a subtle heat effect. Do not depict measured
   individual-cell hotspots or thermal runaway that this model does not compute.
5. Display the operating state and primary limiting reason in plain language
   with text/icon as well as color. Show the requested/allowed difference and
   which candidate limits are binding. Multiple constraints may apply; the
   primary code must retain the engine's original tie precedence.
6. Show Ns x Np and pack V/Ah/kWh in an information view. Any drawn cells are
   representative; the model is a balanced equivalent pack, not individual
   cell simulations. Car movement, wheel RPM, speed, acceleration, road grade
   and driving range are not computed here. Do not fabricate these outputs.
   A stationary car with truthful energy-flow animation is the default.

Build eight chart groups, sharing the same time axis and cursor: SOC;
pack/ambient temperature; requested/allowed current; OCV/terminal voltage;
signed terminal power/ohmic loss; energy received/supplied/lost; nominal
available-energy/headroom estimates; charge/discharge current limits.
Use units, legends and readable tooltips, with markers at profile changes and
state/limiter transitions. Preserve signed values on axes. Provide an event
list for state/reason transitions and a table exposing all 32 channels.
Show efficiency (when applicable), charged/discharged Ah and power-balance
residual in an expandable results area. Export raw CSV with full precision and
a separate JSON run configuration containing version, parameters, inputs,
applied input events, fixed timestep and duration. Never export rounded UI text.
Downsample only chart rendering; keep complete simulation/export data.

Desktop: prominent scene and concise readouts, an adjacent controls panel, and
charts below. Small screens: stack these without clipping labels or controls.
Include keyboard operation, visible focus, accessible names, non-color status
cues and a reduced-motion mode that preserves arrows, labels and all data.
Avoid flashes. Honor prefers-reduced-motion. Do not announce every sample to
assistive technology; announce meaningful status changes and user actions.
Show one concise product note that parameters are illustrative and the output
is a learning simulation. Keep developer details out of the main learner view.

ACCEPTANCE GATES AND REQUIRED DELIVERY
1. Run this file's self-tests before integration and after any engine changes.
   Its embedded tests compare 30 scenario endpoints with native MATLAB results,
   verify selected 32-channel native default samples, and check invariants over
   63,398 sample rows. Seven native invalid settings plus API hardening cases
   must reject cleanly. All statuses 0-6 and reasons 0-4 must be covered.
2. If the native default CSV is accessible, run --compare-csv against it. Require
   all 3601 rows and all 32 channels to agree within 2e-7*(1+abs(reference));
   status/reason/time must agree exactly. Do not widen tolerances to hide errors.
   Other scenarios have embedded native endpoints, not full embedded traces.
   If changing equations or porting language, export full native scenario traces
   and compare every channel; do not describe endpoint tests as full trace parity.
3. Verify UI integration: default 50 -> 75 -> 25% at t=0/1800/3600; idle;
   charge/discharge blocked; all limiter reasons; independent concurrent runs;
   reset; pause/resume; 1x versus 60x identical traces; hidden-tab pause;
   invalid/empty input; edited configuration reset; export; mobile layout;
   reduced motion; and no duplicate timer/listener after unmount/remount.
4. Capture screenshots and a short preview of charging, supplying, derating and
   blocked behavior. Check energy-flow direction, fill, labels and plots against
   the SAME engine sample. Include actual numeric readings in those checks.
5. Deliver working source integrated with platform navigation, the runnable
   preview URL or local start command, numerical/UI test results, visual proof,
   a host-adapter description and any remaining gaps. The handoff kit itself is
   not a completed interface. Do not call the platform work complete until the
   interactive scene, controls, charts and exports are implemented and tested.
   If a host integration is blocked, deliver the runnable module and identify
   the exact missing host interface. Keep completion claims scoped to evidence.

REFERENCE LINKS FOR IMPLEMENTATION DETAILS
https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame
https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion
`;

const freezeDeep = value => {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.values(value).forEach(freezeDeep); Object.freeze(value);
  }
  return value;
};
export const DEFAULT_PARAMETERS = freezeDeep({
  initial_soc_pct: 50, initial_temp_C: 25, ns: 96, np: 24,
  cell_capacity_Ah: 4.2, cell_nominal_V: 3.6, cell_resistance_ohm: 0.016,
  cell_voltage_limits_V: [2.5,4.2], current_ratings_C: [2,2],
  soc_levels_pct: [5,20,80,95], charge_temp_limits_C: [0,10,35,45],
  discharge_temp_limits_C: [-20,0,45,55], mass_kg: 200, cp_J_kgK: 900,
  conductance_W_K: 35, coulombic_efficiencies: [1,1],
  ocv_soc_pct: [0,5,10,20,30,40,50,60,70,80,90,95,100],
  ocv_cell_V: [2.5,3.1,3.3,3.45,3.53,3.6,3.67,3.73,3.8,3.9,4.04,4.12,4.2]
});
export const OUTPUT_FIELDS = Object.freeze([
  'SOC_pct','Temperature_C','Requested_A','Actual_A','OCV_V','Terminal_V',
  'TerminalPower_W','Loss_W','EnergyOut_kWh','EnergyIn_kWh','EnergyLoss_kWh',
  'Available_kWh','Headroom_kWh','ChargeLimit_A','DischargeLimit_A',
  'DischargeEfficiency','ChargeEfficiency','Status','Reason','PowerBalance_W',
  'CellCurrent_A','C_Rate','ChargeIn_Ah','ChargeOut_Ah','ChargeSOCFactor',
  'DischargeSOCFactor','ChargeThermalFactor','DischargeThermalFactor',
  'Ambient_C','HeatToAmbient_W','ChargePower_W','DischargePower_W'
]);
export const STATUS_LABELS = Object.freeze(['Rest','Charging','Supplying load',
  'Charging limited','Supply limited','Charging blocked','Supply blocked']);
export const REASON_LABELS = Object.freeze(['No active restriction','Rated current',
  'State of charge','Temperature','Voltage']);
const assert = (condition,message) => { if (!condition) throw new Error(message); };
const finite = (x,name) => assert(typeof x==='number' && Number.isFinite(x),`${name} must be a finite number.`);
const clip = (x,lo,hi) => Math.min(hi,Math.max(lo,x));
const numberArray = (a,n,name) => {
  assert(Array.isArray(a) && a.length===n,`${name} must contain ${n} numbers.`);
  a.forEach(x=>finite(x,name));
};
const increasing = a => a.slice(1).every((x,i)=>x>a[i]);

export function validateParameters(overrides={}) {
  assert(overrides && typeof overrides==='object' && !Array.isArray(overrides),'Parameters must be an object.');
  for (const key of Object.keys(overrides)) assert(Object.hasOwn(DEFAULT_PARAMETERS,key),`Unknown parameter: ${key}`);
  const p={...DEFAULT_PARAMETERS,...overrides};
  for (const [key,value] of Object.entries(p)) {
    if (Array.isArray(DEFAULT_PARAMETERS[key])) {
      assert(Array.isArray(value),`${key} must be an array.`); p[key]=value.slice();
    } else finite(value,key);
  }
  for (const key of ['ns','np']) assert(Number.isSafeInteger(p[key]) && p[key]>0,`${key} must be a positive whole number.`);
  for (const key of ['cell_capacity_Ah','cell_nominal_V','cell_resistance_ohm','mass_kg','cp_J_kgK']) assert(p[key]>0,`${key} must be positive.`);
  assert(p.conductance_W_K>=0,'Ambient conductance must be nonnegative.');
  for (const key of ['cell_voltage_limits_V','current_ratings_C','coulombic_efficiencies']) numberArray(p[key],2,key);
  for (const key of ['soc_levels_pct','charge_temp_limits_C','discharge_temp_limits_C']) {
    numberArray(p[key],4,key); assert(increasing(p[key]),`${key} must be strictly increasing.`);
  }
  const [vmin,vmax]=p.cell_voltage_limits_V;
  assert(vmin>0 && vmax>vmin,'Cell voltage limits must be positive and increasing.');
  assert(p.cell_nominal_V>=vmin && p.cell_nominal_V<=vmax,'Nominal voltage must be within the voltage limits.');
  assert(p.current_ratings_C.every(x=>x>=0),'C-rates must be nonnegative.');
  assert(p.soc_levels_pct[0]>=0 && p.soc_levels_pct[3]<=100,'SOC limits must be in 0..100%.');
  assert(p.initial_soc_pct>=p.soc_levels_pct[0] && p.initial_soc_pct<=p.soc_levels_pct[3],'Initial SOC must be in the operating window.');
  assert(p.coulombic_efficiencies.every(x=>x>0 && x<=1),'Efficiencies must be in (0,1].');
  assert(p.ocv_soc_pct.length>=2 && p.ocv_soc_pct.length===p.ocv_cell_V.length,'OCV arrays must have equal length >=2.');
  p.ocv_soc_pct.forEach(x=>finite(x,'OCV SOC')); p.ocv_cell_V.forEach(x=>finite(x,'OCV voltage'));
  assert(increasing(p.ocv_soc_pct) && p.ocv_soc_pct[0]===0 && p.ocv_soc_pct.at(-1)===100,'OCV SOC must increase from 0 to 100.');
  assert(p.ocv_cell_V.every((v,i)=>v>=vmin && v<=vmax && (i===0 || v>=p.ocv_cell_V[i-1])),'OCV voltages must be nondecreasing and within limits.');
  return freezeDeep(p);
}

const STATE_KEYS=['t_s','soc','temp_C','energyOut_kWh','energyIn_kWh','energyLoss_kWh','chargeIn_Ah','chargeOut_Ah'];

export function createBatteryModel(overrides={}) {
  const p=validateParameters(overrides);
  const q=p.np*p.cell_capacity_Ah, r=p.ns*p.cell_resistance_ohm/p.np;
  const vnom=p.ns*p.cell_nominal_V, enom=vnom*q/1000;
  const vmin=p.ns*p.cell_voltage_limits_V[0], vmax=p.ns*p.cell_voltage_limits_V[1];
  const cth=p.mass_kg*p.cp_J_kgK, levels=p.soc_levels_pct.map(x=>x/100);
  const rated=p.current_ratings_C.map(x=>x*q), eta=p.coulombic_efficiencies;
  [q,r,vnom,enom,vmin,vmax,cth,...rated].forEach(x=>finite(x,'Derived pack value'));
  assert(q>0 && r>0 && cth>0,'Derived capacity, resistance and thermal capacity must be positive.');
  const pack=freezeDeep({capacity_Ah:q,resistance_ohm:r,nominalVoltage_V:vnom,nominalEnergy_kWh:enom,cellCount:p.ns*p.np});
  function initialState() {
    return Object.freeze({t_s:0,soc:p.initial_soc_pct/100,temp_C:p.initial_temp_C,
      energyOut_kWh:0,energyIn_kWh:0,energyLoss_kWh:0,chargeIn_Ah:0,chargeOut_Ah:0});
  }
  function checkState(s) {
    assert(s && typeof s==='object','State must be an object.');
    STATE_KEYS.forEach(k=>finite(s[k],`State ${k}`));
    assert(Number.isSafeInteger(s.t_s) && s.t_s>=0,'State time must be a nonnegative integer second.');
    assert(s.soc>=levels[0]-1e-12 && s.soc<=levels[3]+1e-12,'State SOC is outside the operating window.');
    STATE_KEYS.slice(3).forEach(k=>assert(s[k]>=0,`State ${k} must be nonnegative.`));
  }
  function ocvAt(soc) {
    const z=clip(soc*100,0,100), xs=p.ocv_soc_pct, vs=p.ocv_cell_V;
    let i=0; while (i<xs.length-2 && z>xs[i+1]) i++;
    return p.ns*(vs[i]+(z-xs[i])*(vs[i+1]-vs[i])/(xs[i+1]-xs[i]));
  }
  const thermalFactor=(temp,a)=>clip(Math.min((temp-a[0])/(a[1]-a[0]),(a[3]-temp)/(a[3]-a[2])),0,1);
  function observe(s,input) {
    checkState(s); assert(input && typeof input==='object','Input is required.');
    const req=input.requestedCurrentA, ambient=input.ambientC;
    finite(req,'Requested current'); finite(ambient,'Ambient temperature');
    const ocv=ocvAt(s.soc);
    const sf=[clip((levels[3]-s.soc)/(levels[3]-levels[2]),0,1),clip((s.soc-levels[0])/(levels[1]-levels[0]),0,1)];
    const tf=[thermalFactor(s.temp_C,p.charge_temp_limits_C),thermalFactor(s.temp_C,p.discharge_temp_limits_C)];
    const socLimit=sf.map((f,i)=>f*rated[i]);
    const thermal=tf.map((f,i)=>f*rated[i]);
    const voltage=[Math.max(0,(vmax-ocv)/r),Math.max(0,(ocv-vmin)/r)];
    const guard=[Math.max(0,(levels[3]-s.soc)*q*3600/eta[0]),Math.max(0,(s.soc-levels[0])*q*3600*eta[1])];
    const combinedSoc=socLimit.map((x,i)=>Math.min(x,guard[i]));
    const limits=rated.map((x,i)=>Math.min(x,socLimit[i],thermal[i],voltage[i],guard[i]));
    const current=clip(req,-limits[0],limits[1]);
    const terminal=ocv-current*r, power=terminal*current, loss=current*current*r;
    const dischargePower=Math.max(0,power), chargePower=Math.max(0,-power);
    const dischargeEfficiency=dischargePower>1e-9 ? dischargePower/(dischargePower+loss) : -1;
    const chargeEfficiency=chargePower>1e-9 ? Math.max(0,(chargePower-loss)/chargePower) : -1;
    const direction=req<0?0:1, limited=Math.abs(req-current)>1e-8;
    let status=direction+1;
    if(limited) status=direction+3;
    if(Math.abs(current)<=1e-8) status=direction+5;
    if(Math.abs(req)<=1e-8) status=0;
    let reason=0;
    if(limited) {
      reason=1;
      if(voltage[direction]<rated[direction]-1e-8) reason=4;
      if(combinedSoc[direction]<rated[direction]-1e-8 && combinedSoc[direction]<=limits[direction]+1e-8) reason=2;
      // Correct Boolean AND: reduced AND binding, for the active direction.
      if(thermal[direction]<rated[direction]-1e-8 && thermal[direction]<=limits[direction]+1e-8) reason=3;
    }
    const heat=p.conductance_W_K*(s.temp_C-ambient);
    const values=[s.soc*100,s.temp_C,req,current,ocv,terminal,power,loss,
      s.energyOut_kWh,s.energyIn_kWh,s.energyLoss_kWh,Math.max(0,s.soc-levels[0])*enom,
      Math.max(0,levels[3]-s.soc)*enom,...limits,dischargeEfficiency,chargeEfficiency,status,reason,
      ocv*current-power-loss,current/p.np,current/q,s.chargeIn_Ah,s.chargeOut_Ah,...sf,...tf,
      ambient,heat,chargePower,dischargePower];
    values.forEach((x,i)=>finite(x,OUTPUT_FIELDS[i]));
    const candidates={rated,soc:socLimit,temperature:thermal,voltage,oneStepSOC:guard};
    const bindingLimits=limited?Object.entries(candidates).filter(([,v])=>v[direction]<=limits[direction]+1e-8).map(([name])=>name):[];
    return freezeDeep({Time_s:s.t_s,...Object.fromEntries(OUTPUT_FIELDS.map((name,i)=>[name,values[i]])),
      diagnostics:{candidateLimitsA:candidates,bindingLimits,limited,primaryReason:REASON_LABELS[reason]}});
  }
  function step(s,input) {
    const output=observe(s,input), current=output.Actual_A;
    const effective=current<0?current*eta[0]:current/eta[1];
    const nextState=Object.freeze({t_s:s.t_s+1,soc:clip(s.soc-effective/(q*3600),levels[0],levels[3]),
      temp_C:s.temp_C+(output.Loss_W-output.HeatToAmbient_W)/cth,
      energyOut_kWh:s.energyOut_kWh+output.DischargePower_W/3.6e6,
      energyIn_kWh:s.energyIn_kWh+output.ChargePower_W/3.6e6,
      energyLoss_kWh:s.energyLoss_kWh+output.Loss_W/3.6e6,
      chargeIn_Ah:s.chargeIn_Ah+Math.max(0,-current)/3600,
      chargeOut_Ah:s.chargeOut_Ah+Math.max(0,current)/3600});
    checkState(nextState);
    return {output,nextState};
  }
  return Object.freeze({parameters:p,pack,initialState,observe,step});
}

export function deriveViewModel(output) {
  const direction=Math.abs(output.Actual_A)<=1e-8?'none':output.Actual_A<0?'intoBattery':'outOfBattery';
  return Object.freeze({timeSeconds:output.Time_s,socPercent:output.SOC_pct,temperatureC:output.Temperature_C,
    requestedAmps:output.Requested_A,allowedAmps:output.Actual_A,terminalPowerKW:output.TerminalPower_W/1000,
    flowDirection:direction,flowPowerKW:direction==='none'?0:Math.abs(output.TerminalPower_W)/1000,
    heatLossKW:output.Loss_W/1000,rejectedAmps:Math.abs(output.Requested_A-output.Actual_A),
    statusText:STATUS_LABELS[output.Status],reasonText:REASON_LABELS[output.Reason],
    chargeEfficiencyPercent:output.ChargeEfficiency<0?null:100*output.ChargeEfficiency,
    dischargeEfficiencyPercent:output.DischargeEfficiency<0?null:100*output.DischargeEfficiency,
    bindingLimits:output.diagnostics.bindingLimits});
}
export const outputToRow = output => [output.Time_s,...OUTPUT_FIELDS.map(name=>output[name])];
export const rowsToCsv = rows => [['Time_s',...OUTPUT_FIELDS].join(','),...rows.map(row=>row.join(','))].join('\n')+'\n';

export function runScenario(spec={}, {collect=true,onSample}={}) {
  const {parameters={},beforeA=-50.4,afterA=100.8,stepTimeS=1800,durationS=3600,ambientC=25}=spec;
  [beforeA,afterA,stepTimeS,durationS,ambientC].forEach(x=>finite(x,'Scenario input'));
  assert(Number.isSafeInteger(durationS) && durationS>=0,'Duration must be a nonnegative integer second.');
  assert(Number.isSafeInteger(stepTimeS) && stepTimeS>=0,'Step time must be a nonnegative integer second.');
  const model=createBatteryModel(parameters), rows=[];
  let state=model.initialState(), first,last;
  for(let t=0;t<=durationS;t++) {
    const input={requestedCurrentA:t<stepTimeS?beforeA:afterA,ambientC};
    let output;
    if(t===durationS) output=model.observe(state,input);
    else { const result=model.step(state,input); output=result.output; state=result.nextState; }
    if(t===0) first=output; last=output;
    if(collect) rows.push(outputToRow(output));
    if(onSample) onSample(output,model);
  }
  return {rows,first,last,state,parameters:model.parameters};
}

// Native MATLAB fixture records are embedded below; no source file is needed.
export const MATLAB_SUMMARIES = freezeDeep({
  "default_cycle": {
    "samples": 3601,
    "final_soc_pct": 25.0000000000011,
    "initial_current_A": -50.4,
    "initial_status": 1,
    "initial_reason": 0,
    "max_reference_error": 1.45519152283669e-11,
    "max_power_balance_error_W": 3.75166564481333e-12
  },
  "rest": {
    "samples": 3601,
    "final_soc_pct": 50.0,
    "initial_current_A": 0.0,
    "initial_status": 0,
    "initial_reason": 0,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "charge": {
    "samples": 601,
    "final_soc_pct": 58.3333333333346,
    "initial_current_A": -50.4,
    "initial_status": 1,
    "initial_reason": 0,
    "max_reference_error": 3.63797880709171e-12,
    "max_power_balance_error_W": 2.70006239588838e-12
  },
  "discharge": {
    "samples": 601,
    "final_soc_pct": 33.3333333333341,
    "initial_current_A": 100.8,
    "initial_status": 2,
    "initial_reason": 0,
    "max_reference_error": 1.45519152283669e-11,
    "max_power_balance_error_W": 3.75166564481333e-12
  },
  "rated_charge": {
    "samples": 301,
    "final_soc_pct": 66.6666666666659,
    "initial_current_A": -201.6,
    "initial_status": 3,
    "initial_reason": 1,
    "max_reference_error": 2.91038304567337e-11,
    "max_power_balance_error_W": 4.54747350886464e-13
  },
  "rated_discharge": {
    "samples": 301,
    "final_soc_pct": 33.3333333333341,
    "initial_current_A": 201.6,
    "initial_status": 4,
    "initial_reason": 1,
    "max_reference_error": 1.45519152283669e-11,
    "max_power_balance_error_W": 4.54747350886464e-13
  },
  "soc_charge_taper": {
    "samples": 601,
    "final_soc_pct": 94.4603905951427,
    "initial_current_A": -67.2,
    "initial_status": 3,
    "initial_reason": 2,
    "max_reference_error": 7.27595761418343e-12,
    "max_power_balance_error_W": 4.49063009000383e-12
  },
  "soc_discharge_taper": {
    "samples": 601,
    "final_soc_pct": 5.53960940485737,
    "initial_current_A": 67.2,
    "initial_status": 4,
    "initial_reason": 2,
    "max_reference_error": 7.27595761418343e-12,
    "max_power_balance_error_W": 4.2632564145606e-12
  },
  "soc_charge_stop": {
    "samples": 121,
    "final_soc_pct": 95.0,
    "initial_current_A": -0.0,
    "initial_status": 5,
    "initial_reason": 2,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "soc_discharge_stop": {
    "samples": 121,
    "final_soc_pct": 5.0,
    "initial_current_A": 0.0,
    "initial_status": 6,
    "initial_reason": 2,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "charge_cold_stop": {
    "samples": 121,
    "final_soc_pct": 50.0,
    "initial_current_A": -0.0,
    "initial_status": 5,
    "initial_reason": 3,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "charge_hot_stop": {
    "samples": 121,
    "final_soc_pct": 50.0,
    "initial_current_A": -0.0,
    "initial_status": 5,
    "initial_reason": 3,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "discharge_cold_stop": {
    "samples": 121,
    "final_soc_pct": 50.0,
    "initial_current_A": 0.0,
    "initial_status": 6,
    "initial_reason": 3,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "discharge_hot_stop": {
    "samples": 121,
    "final_soc_pct": 50.0,
    "initial_current_A": 0.0,
    "initial_status": 6,
    "initial_reason": 3,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "charge_cold_ramp": {
    "samples": 301,
    "final_soc_pct": 59.366112310487,
    "initial_current_A": -100.8,
    "initial_status": 3,
    "initial_reason": 3,
    "max_reference_error": 1.45519152283669e-11,
    "max_power_balance_error_W": 9.54969436861575e-12
  },
  "charge_hot_ramp": {
    "samples": 301,
    "final_soc_pct": 57.558703052913,
    "initial_current_A": -100.8,
    "initial_status": 3,
    "initial_reason": 3,
    "max_reference_error": 7.27595761418343e-12,
    "max_power_balance_error_W": 8.07176547823474e-12
  },
  "discharge_cold_ramp": {
    "samples": 301,
    "final_soc_pct": 41.1910293314589,
    "initial_current_A": 100.8,
    "initial_status": 4,
    "initial_reason": 3,
    "max_reference_error": 1.45519152283669e-11,
    "max_power_balance_error_W": 9.43600753089413e-12
  },
  "discharge_hot_ramp": {
    "samples": 301,
    "final_soc_pct": 42.441296947087,
    "initial_current_A": 100.8,
    "initial_status": 4,
    "initial_reason": 3,
    "max_reference_error": 7.27595761418343e-12,
    "max_power_balance_error_W": 8.18545231595635e-12
  },
  "charge_voltage_limit": {
    "samples": 301,
    "final_soc_pct": 56.3346207361641,
    "initial_current_A": -79.5000000000001,
    "initial_status": 3,
    "initial_reason": 4,
    "max_reference_error": 4.00177668780088e-11,
    "max_power_balance_error_W": 3.63797880709171e-12
  },
  "discharge_voltage_limit": {
    "samples": 301,
    "final_soc_pct": 44.2957044922454,
    "initial_current_A": 70.2,
    "initial_status": 4,
    "initial_reason": 4,
    "max_reference_error": 1.09139364212751e-11,
    "max_power_balance_error_W": 3.63797880709171e-12
  },
  "zero_charge_rating": {
    "samples": 121,
    "final_soc_pct": 50.0,
    "initial_current_A": -0.0,
    "initial_status": 5,
    "initial_reason": 1,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "zero_discharge_rating": {
    "samples": 121,
    "final_soc_pct": 50.0,
    "initial_current_A": 0.0,
    "initial_status": 6,
    "initial_reason": 1,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "nonunit_efficiency": {
    "samples": 1201,
    "final_soc_pct": 37.8921568627477,
    "initial_current_A": -50.4,
    "initial_status": 1,
    "initial_reason": 0,
    "max_reference_error": 1.45519152283669e-11,
    "max_power_balance_error_W": 3.75166564481333e-12
  },
  "different_pack": {
    "samples": 1201,
    "final_soc_pct": 41.666666666667,
    "initial_current_A": -25.2,
    "initial_status": 1,
    "initial_reason": 0,
    "max_reference_error": 3.63797880709171e-12,
    "max_power_balance_error_W": 9.37916411203332e-13
  },
  "long_charge": {
    "samples": 21601,
    "final_soc_pct": 94.9999999999985,
    "initial_current_A": -201.6,
    "initial_status": 1,
    "initial_reason": 0,
    "max_reference_error": 2.91038304567337e-11,
    "max_power_balance_error_W": 1.40971678774804e-11
  },
  "long_discharge": {
    "samples": 21601,
    "final_soc_pct": 5.00000000000009,
    "initial_current_A": 201.6,
    "initial_status": 2,
    "initial_reason": 0,
    "max_reference_error": 1.45519152283669e-11,
    "max_power_balance_error_W": 1.40971678774804e-11
  },
  "charge_one_step_guard": {
    "samples": 5,
    "final_soc_pct": 95.0,
    "initial_current_A": -362.87999999996,
    "initial_status": 3,
    "initial_reason": 2,
    "max_reference_error": 5.82076609134674e-11,
    "max_power_balance_error_W": 7.05644375396941e-12
  },
  "discharge_one_step_guard": {
    "samples": 5,
    "final_soc_pct": 5.0,
    "initial_current_A": 362.879999999998,
    "initial_status": 4,
    "initial_reason": 2,
    "max_reference_error": 1.45519152283669e-11,
    "max_power_balance_error_W": 7.05633424954999e-12
  },
  "ambient_cooling": {
    "samples": 3601,
    "final_soc_pct": 50.0,
    "initial_current_A": 0.0,
    "initial_status": 0,
    "initial_reason": 0,
    "max_reference_error": 0.0,
    "max_power_balance_error_W": 0.0
  },
  "no_ambient_transfer": {
    "samples": 1201,
    "final_soc_pct": 50.0,
    "initial_current_A": -100.0,
    "initial_status": 1,
    "initial_reason": 0,
    "max_reference_error": 1.45519152283669e-11,
    "max_power_balance_error_W": 7.27595761418343e-12
  }
});
export const MATLAB_DEFAULT_CHECKPOINTS = freezeDeep({
  "0": [
    0.0,
    50.0,
    25.0,
    -50.4,
    -50.4,
    352.32,
    355.5456,
    -17919.49824,
    162.57024,
    0.0,
    0.0,
    0.0,
    15.676416,
    15.676416,
    201.6,
    201.6,
    -1.0,
    0.990927745976887,
    1.0,
    0.0,
    -2.70006239588838e-12,
    -2.1,
    -0.5,
    0.0,
    0.0,
    1.0,
    1.0,
    1.0,
    1.0,
    25.0,
    0.0,
    17919.49824,
    0.0
  ],
  "1": [
    1.0,
    50.0138888888889,
    25.000903168,
    -50.4,
    -50.4,
    352.328,
    355.5536,
    -17919.90144,
    162.57024,
    0.0,
    0.0049776384,
    4.51584e-05,
    15.6812544,
    15.6715776,
    201.6,
    201.6,
    -1.0,
    0.990927950103725,
    1.0,
    0.0,
    9.37916411203332e-13,
    -2.1,
    -0.5,
    0.014,
    0.0,
    1.0,
    1.0,
    1.0,
    1.0,
    25.0,
    0.0316108800000237,
    17919.90144,
    0.0
  ],
  "900": [
    900.0,
    62.500000000002,
    25.7457666526561,
    -50.4,
    -50.4,
    359.760000000001,
    362.985600000001,
    -18294.4742400001,
    162.57024,
    0.0,
    4.52548488000001,
    0.0406425599999999,
    20.0309760000007,
    11.3218559999993,
    201.6,
    201.6,
    -1.0,
    0.991113697072281,
    1.0,
    0.0,
    9.37916411203332e-13,
    -2.1,
    -0.5,
    12.5999999999998,
    0.0,
    1.0,
    1.0,
    1.0,
    1.0,
    25.0,
    26.1018328429644,
    18294.4742400001,
    0.0
  ],
  "1799": [
    1799.0,
    74.986111111115,
    26.3711584985872,
    -50.4,
    -50.4,
    369.58666666667,
    372.81226666667,
    -18789.7382400002,
    162.57024,
    0.0,
    9.1503639882667,
    0.0812399615999987,
    24.3806976000014,
    6.97213439999864,
    201.6,
    201.6,
    -1.0,
    0.991347924174169,
    1.0,
    0.0,
    -2.70006239588838e-12,
    -2.1,
    -0.5,
    25.1859999999992,
    0.0,
    1.0,
    1.0,
    1.0,
    1.0,
    25.0,
    47.9905474505519,
    18789.7382400002,
    0.0
  ],
  "1800": [
    1800.0,
    75.0000000000039,
    26.3717950524347,
    100.8,
    100.8,
    369.600000000004,
    363.148800000004,
    36605.3990400004,
    650.28096,
    0.0,
    9.15558336000004,
    0.0812851199999987,
    24.3855360000014,
    6.96729599999864,
    201.6,
    201.6,
    0.982545454545455,
    -1.0,
    2.0,
    0.0,
    3.75166564481333e-12,
    4.2,
    1.0,
    25.1999999999992,
    0.0,
    1.0,
    1.0,
    1.0,
    1.0,
    25.0,
    48.0128268352142,
    0.0,
    36605.3990400004
  ],
  "1801": [
    1801.0,
    74.9722222222261,
    26.3751409865078,
    100.8,
    100.8,
    369.573333333337,
    363.122133333337,
    36602.7110400004,
    650.28096,
    0.0101681664000001,
    9.15558336000004,
    0.0814657535999987,
    24.3758592000014,
    6.97697279999864,
    201.6,
    201.6,
    0.982544195107872,
    -1.0,
    2.0,
    0.0,
    -3.5242919693701e-12,
    4.2,
    1.0,
    25.1999999999992,
    0.028,
    1.0,
    1.0,
    1.0,
    1.0,
    25.0,
    48.1299345277741,
    0.0,
    36602.7110400004
  ],
  "2700": [
    2700.0,
    50.0,
    29.134610003509,
    100.8,
    100.8,
    352.32,
    345.8688,
    34863.57504,
    650.28096,
    8.91209088000004,
    9.15558336000004,
    0.243855360000002,
    15.676416,
    15.676416,
    201.6,
    201.6,
    0.981689373297003,
    -1.0,
    2.0,
    0.0,
    3.75166564481333e-12,
    4.2,
    1.0,
    25.1999999999992,
    25.1999999999996,
    1.0,
    1.0,
    1.0,
    1.0,
    25.0,
    144.711350122817,
    0.0,
    34863.57504
  ],
  "3599": [
    3599.0,
    25.0277777777789,
    31.4514767285958,
    100.8,
    100.8,
    335.061333333334,
    328.610133333334,
    33123.9014400001,
    650.28096,
    17.4061358762667,
    9.15558336000004,
    0.406244966399985,
    6.97697280000038,
    24.3758591999996,
    201.6,
    201.6,
    0.980746211638864,
    -1.0,
    2.0,
    0.0,
    3.75166564481333e-12,
    4.2,
    1.0,
    25.1999999999992,
    50.3719999999985,
    1.0,
    1.0,
    1.0,
    1.0,
    25.0,
    225.801685500853,
    0.0,
    33123.9014400001
  ],
  "3600": [
    3600.0,
    25.0000000000011,
    31.4538349467875,
    100.8,
    100.8,
    335.040000000001,
    328.588800000001,
    33121.7510400001,
    650.28096,
    17.41533696,
    9.15558336000004,
    0.406425599999985,
    6.96729600000038,
    24.3855359999996,
    201.6,
    201.6,
    0.980744985673353,
    -1.0,
    2.0,
    0.0,
    3.75166564481333e-12,
    4.2,
    1.0,
    25.1999999999992,
    50.3999999999985,
    1.0,
    1.0,
    1.0,
    1.0,
    25.0,
    225.884223137562,
    0.0,
    33121.7510400001
  ]
});

export const REGRESSION_SCENARIOS = freezeDeep([
  ['default_cycle',-50.4,100.8,1800,3600,{}],
  ['rest',0,0,1800,3600,{}],['charge',-50.4,-50.4,1800,600,{}],['discharge',100.8,100.8,1800,600,{}],
  ['rated_charge',-400,-400,1800,300,{}],['rated_discharge',400,400,1800,300,{}],
  ['soc_charge_taper',-200,-200,1800,600,{initial_soc_pct:90}],
  ['soc_discharge_taper',200,200,1800,600,{initial_soc_pct:10}],
  ['soc_charge_stop',-100,-100,1800,120,{initial_soc_pct:95}],
  ['soc_discharge_stop',100,100,1800,120,{initial_soc_pct:5}],
  ['charge_cold_stop',-100,-100,1800,120,{initial_temp_C:0}],
  ['charge_hot_stop',-100,-100,1800,120,{initial_temp_C:45}],
  ['discharge_cold_stop',100,100,1800,120,{initial_temp_C:-20}],
  ['discharge_hot_stop',100,100,1800,120,{initial_temp_C:55}],
  ['charge_cold_ramp',-200,-200,1800,300,{initial_temp_C:5}],
  ['charge_hot_ramp',-200,-200,1800,300,{initial_temp_C:40}],
  ['discharge_cold_ramp',200,200,1800,300,{initial_temp_C:-10}],
  ['discharge_hot_ramp',200,200,1800,300,{initial_temp_C:50}],
  ['charge_voltage_limit',-200,-200,1800,300,{cell_resistance_ohm:0.16}],
  ['discharge_voltage_limit',200,200,1800,300,{cell_resistance_ohm:0.4}],
  ['zero_charge_rating',-100,-100,1800,120,{current_ratings_C:[0,2]}],
  ['zero_discharge_rating',100,100,1800,120,{current_ratings_C:[2,0]}],
  ['nonunit_efficiency',-50.4,100.8,600,1200,{coulombic_efficiencies:[0.9,0.85]}],
  ['different_pack',-25.2,50.4,600,1200,{ns:48,np:12}],
  ['long_charge',-201.6,-201.6,1800,21600,{}],['long_discharge',201.6,201.6,1800,21600,{}],
  ['charge_one_step_guard',-1e6,-1e6,1800,4,{initial_soc_pct:94.9,current_ratings_C:[1e5,1e5],cell_resistance_ohm:1e-9}],
  ['discharge_one_step_guard',1e6,1e6,1800,4,{initial_soc_pct:5.1,current_ratings_C:[1e5,1e5],cell_resistance_ohm:1e-9}],
  ['ambient_cooling',0,0,1800,3600,{initial_temp_C:40},20],
  ['no_ambient_transfer',-100,100,600,1200,{conductance_W_K:0}]
]);

function near(actual,expected,label) {
  assert(Number.isFinite(actual) && Number.isFinite(expected) && Math.abs(actual-expected)<=2e-7*(1+Math.abs(expected)),`${label}: ${actual} != ${expected}`);
}
function expectThrow(fn,label) {
  let rejected=false; try { fn(); } catch { rejected=true; }
  assert(rejected,`Invalid input was accepted: ${label}`);
}
export function runSelfTests() {
  const statuses=new Set(), reasons=new Set(), results=[];
  let samples=0,maxPowerResidual=0;
  for(const [name,beforeA,afterA,stepTimeS,durationS,parameters,ambientOverride] of REGRESSION_SCENARIOS) {
    let previous;
    const ambientC=ambientOverride??parameters.initial_temp_C??25;
    const result=runScenario({beforeA,afterA,stepTimeS,durationS,parameters,ambientC},{collect:false,onSample:(o,model)=>{
      samples++; statuses.add(o.Status); reasons.add(o.Reason);
      const p=model.parameters;
      assert(OUTPUT_FIELDS.every(key=>Number.isFinite(o[key])),`${name}: nonfinite result`);
      assert(o.SOC_pct>=p.soc_levels_pct[0]-1e-8 && o.SOC_pct<=p.soc_levels_pct[3]+1e-8,`${name}: SOC bounds`);
      assert(o.Terminal_V>=p.ns*p.cell_voltage_limits_V[0]-1e-7 && o.Terminal_V<=p.ns*p.cell_voltage_limits_V[1]+1e-7,`${name}: voltage bounds`);
      assert(o.Actual_A>=-o.ChargeLimit_A-1e-8 && o.Actual_A<=o.DischargeLimit_A+1e-8,`${name}: current bounds`);
      assert(Math.abs(o.PowerBalance_W)<1e-7,`${name}: power balance`);
      maxPowerResidual=Math.max(maxPowerResidual,Math.abs(o.PowerBalance_W));
      if(previous) {
        assert(o.Time_s===previous.Time_s+1,'Incorrect time grid');
        for(const key of ['EnergyOut_kWh','EnergyIn_kWh','EnergyLoss_kWh','ChargeIn_Ah','ChargeOut_Ah']) assert(o[key]>=previous[key]-1e-10,`${name}: decreasing ${key}`);
        near(o.EnergyIn_kWh-previous.EnergyIn_kWh,previous.ChargePower_W/3.6e6,`${name}: charge energy timing`);
        near(o.EnergyOut_kWh-previous.EnergyOut_kWh,previous.DischargePower_W/3.6e6,`${name}: discharge energy timing`);
      }
      if(name==='default_cycle' && Object.hasOwn(MATLAB_DEFAULT_CHECKPOINTS,o.Time_s)) {
        outputToRow(o).forEach((v,i)=>near(v,MATLAB_DEFAULT_CHECKPOINTS[o.Time_s][i],`Native checkpoint ${o.Time_s} column ${i}`));
      }
      previous=o;
    }});
    const native=MATLAB_SUMMARIES[name];
    assert(native && durationS+1===native.samples,`${name}: native scenario missing`);
    near(result.last.SOC_pct,native.final_soc_pct,`${name}: final SOC`);
    near(result.first.Actual_A,native.initial_current_A,`${name}: initial current`);
    assert(result.first.Status===native.initial_status && result.first.Reason===native.initial_reason,`${name}: status/reason`);
    assert(result.state.t_s===durationS,`${name}: extra final integration`);
    results.push({scenario:name,samples:durationS+1,finalSOC:result.last.SOC_pct,pass:true});
  }
  assert([...statuses].sort().join(',')==='0,1,2,3,4,5,6','Incomplete status coverage');
  assert([...reasons].sort().join(',')==='0,1,2,3,4','Incomplete reason coverage');
  const invalid=[{np:0},{cell_resistance_ohm:0},{soc_levels_pct:[5,20,20,95]},
    {initial_soc_pct:101},{coulombic_efficiencies:[1,0]},{charge_temp_limits_C:[0,10,10,45]},
    {ocv_soc_pct:[0,50,40,100]},{ns:true},{mass_kg:''},{np:NaN},{initial_temp_C:Infinity},
    {current_ratings_C:[[2],2]},{unknownParameter:1},{ocv_cell_V:[]},{np:1.5}];
  invalid.forEach((p,i)=>expectThrow(()=>createBatteryModel(p),`parameter case ${i}`));
  const model=createBatteryModel(), initial=model.initialState(), input={requestedCurrentA:-50.4,ambientC:25};
  for(const bad of [NaN,Infinity,'',true,undefined]) expectThrow(()=>model.observe(initial,{...input,requestedCurrentA:bad}),'invalid current');
  expectThrow(()=>model.observe({...initial,t_s:0.5},input),'fractional state time');
  expectThrow(()=>model.observe(initial,{...input,ambientC:NaN}),'invalid ambient');
  expectThrow(()=>runScenario({durationS:0.5}),'fractional duration');
  expectThrow(()=>runScenario({stepTimeS:-1}),'negative step time');
  const before=JSON.stringify(initial), a=model.step(initial,input), b=model.step(initial,input);
  assert(JSON.stringify(initial)===before && JSON.stringify(a)===JSON.stringify(b),'State mutated or step nondeterministic');
  const zero=runScenario({durationS:0}); assert(zero.rows.length===1 && zero.state.t_s===0,'Zero duration');
  const blocked=createBatteryModel({initial_soc_pct:95});
  const blockedView=deriveViewModel(blocked.observe(blocked.initialState(),input));
  assert(blockedView.flowDirection==='none' && blockedView.chargeEfficiencyPercent===null,'Blocked display semantics');
  return {pass:true,scenarioCount:results.length,sampleCount:samples,nativeInvalidParameterCases:7,
    extraInvalidParameterCases:invalid.length-7,invalidInputCases:9,selectedNativeCheckpoints:Object.keys(MATLAB_DEFAULT_CHECKPOINTS).length,
    allStatuses:true,allReasons:true,maxPowerBalanceResidualW:maxPowerResidual,scenarios:results};
}

export function compareDefaultCsv(text) {
  const lines=text.replace(/^\uFEFF/,'').trim().split(/\r?\n/);
  assert(lines[0]===['Time_s',...OUTPUT_FIELDS].join(','),'CSV channel order does not match the native default export.');
  const reference=lines.slice(1).map(line=>line.split(',').map(Number));
  const actual=runScenario().rows;
  assert(reference.length===actual.length,'CSV sample count must be 3601.');
  let maxAbsoluteError=0;
  actual.forEach((row,i)=>{
    assert(reference[i].length===33,'CSV row must contain time plus 32 outputs.');
    row.forEach((value,j)=>{
      near(value,reference[i][j],`t=${i} column=${j}`);
      if(j===0 || j===18 || j===19) assert(value===reference[i][j],`Discrete channel mismatch at t=${i}`);
      maxAbsoluteError=Math.max(maxAbsoluteError,Math.abs(value-reference[i][j]));
    });
  });
  return {pass:true,rows:actual.length,channels:32,numericComparisons:actual.length*32,maxAbsoluteError};
}

// Node-only CLI. Browser import does not use Node APIs, start loops or fetch data.
if(typeof process!=='undefined' && process.versions?.node && process.argv[1]) {
  const {pathToFileURL}=await import('node:url');
  if(import.meta.url===pathToFileURL(process.argv[1]).href) {
    try {
      const [command,arg]=process.argv.slice(2);
      if(command==='--brief') console.log(CODEX_IMPLEMENTATION_BRIEF);
      else if(command==='--self-test') console.log(JSON.stringify(runSelfTests(),null,2));
      else if(command==='--compare-csv') {
        assert(arg,'Supply the native default CSV path.');
        const {readFile}=await import('node:fs/promises');
        console.log(JSON.stringify(compareDefaultCsv(await readFile(arg,'utf8')),null,2));
      } else if(command==='--write-csv') {
        assert(arg,'Supply a new output CSV path.');
        const {writeFile}=await import('node:fs/promises');
        await writeFile(arg,rowsToCsv(runScenario().rows),{encoding:'utf8',flag:'wx'});
        console.log(`Wrote default simulation to ${arg}`);
      } else {
        assert(!command || command==='--help',`Unknown option: ${command}`);
        console.log('Usage: node battery-platform-kit.mjs --self-test | --brief | --compare-csv NATIVE.csv | --write-csv NEW.csv');
      }
    } catch(error) { console.error(error.message); process.exitCode=1; }
  }
}
```
<!-- END_EXECUTABLE_ENGINE -->
