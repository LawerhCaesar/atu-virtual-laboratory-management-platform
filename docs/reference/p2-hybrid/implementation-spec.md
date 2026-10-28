# Codex Project Instructions: P2 Full-Parallel Hybrid Virtual Platform

## 1. Mission

Build and integrate a user-friendly virtual-platform module that reproduces the delivered MATLAB/Simulink model named:

`Lawrence_Andoh_P2_Hybrid_Torque_Intensity_Model.slx`

The module shall convert the validated control-oriented Simulink logic into normal application code that runs without MATLAB or a Simulink runtime. It shall let a user change the same approved inputs, run the simulation, inspect the same scientific outputs, compare low/medium/high torque cases, and export the results.

The implementation must be scientifically traceable, visually clear, deterministic, testable, and suitable for integration into the existing automotive virtual platform.

## 2. Source-of-Truth Order

Use the following order when sources disagree:

1. `reference/Lawrence_Andoh_P2_Hybrid_Torque_Intensity_Model.slx`
2. `reference/Lawrence_Andoh_P2_Hybrid_Model_Data_and_Testing_Guide.docx`
3. This `AGENTS.md`
4. `reference/Lawrence_Andoh_Chapters_1_to_3_Revised.pdf` or the latest approved thesis document
5. Optional conversation reference below

Do not silently broaden the implemented model from thesis descriptions that are not present in the delivered `.slx` model. Phase 1 is an exact software conversion of the executed P2 model, not a new P3/P4, regenerative-braking, drive-cycle, fuel-map, thermal, or battery-ageing model.

## 3. Optional Conversation Reference

Optional ChatGPT conversation share URL:

`CHAT_REFERENCE_URL = "PASTE_SHARED_CHATGPT_CONVERSATION_URL_HERE"`

If the placeholder is not replaced or the link cannot be opened, continue from the local source files and this specification. The implementation must not depend on access to the chat.

## 4. First Actions for Codex

Before editing code:

1. Inspect the repository, existing platform architecture, build scripts, coding conventions, routes, authentication, themes, chart libraries, test tools, and deployment method.
2. Locate the source files listed above. If their folder differs, update internal references without changing the files.
3. Write a concise implementation plan that identifies the existing stack and the smallest integration path.
4. Preserve the existing platform stack where practical. Do not replace a working architecture merely to use the fallback stack below.
5. Implement, run tests, launch the application, and validate the actual interface in a browser.

## 5. Technology Selection

### 5.1 Existing Repository

If the virtual platform already has a backend and frontend, integrate into that stack. Keep the simulation logic in a pure, independently testable module separated from HTTP, UI, storage, and chart code.

### 5.2 Empty or Prototype Repository

Use this fallback only when no established application stack exists:

- Backend: Python with FastAPI, Pydantic, NumPy, and pytest.
- Frontend: React with TypeScript and the repository's preferred build tool.
- Charts: the platform's existing chart package; otherwise use ECharts or Plotly.
- Technical animation: SVG and CSS/React animation by default.
- Optional 3D: Three.js/react-three-fiber only as a secondary enhancement, never as a dependency for the scientific results.

Do not require MATLAB in production. Do not execute the `.slx` file at runtime. The `.slx` and guide are reference artefacts only.

## 6. Phase-1 Scientific Boundary

Implement the exact delivered model boundary:

- One P2 full-parallel hybrid arrangement.
- Constant requested transmission-input torque during each run.
- Constant motor speed during each run.
- User-selected initial battery state of charge.
- Rule-based low, medium, and high torque classification.
- Engine-motor torque allocation.
- P2 clutch-state logic.
- Transmission/final-drive wheel-torque conversion.
- Motor mechanical power and electrical conversion.
- Simple open-circuit-voltage plus internal-resistance battery model.
- Battery current, terminal voltage, SOC depletion, I-squared-R loss, energy use, energy efficiency, RMS current, torque error, and torque RMSE.
- Time-series results, final summary, comparison, visualisation, and export.

Explicit Phase-1 non-goals:

- Negative requested torque and regenerative braking.
- Friction braking, ABS, EBD, ESC, or tyre slip.
- P3 or P4 architectures.
- Engine fuel consumption, BSFC maps, emissions, or engine-start transients.
- Plug-in charge-depleting/charge-sustaining operation beyond initial SOC.
- Vehicle longitudinal speed, distance, acceleration, road gradient, or drive cycles.
- 2-RC battery polarisation, pack thermal dynamics, degradation, or cell balancing.
- Production control, calibration, certification, or safety validation.

Provide clean extension interfaces for these future features, but do not present them as implemented or validated.

## 7. Exact Model Parameters

Expose defaults and units in one typed configuration object. Avoid hidden constants.

| Parameter | Symbol/API key | Default | Unit |
|---|---|---:|---|
| Low-torque threshold | `low_torque_threshold_nm` | 80 | Nm |
| High-torque threshold | `high_torque_threshold_nm` | 200 | Nm |
| Low-torque motor share | `low_torque_motor_share` | 1.00 | fraction |
| Blended motor share | `blended_motor_share` | 0.50 | fraction |
| Engine maximum torque | `engine_max_torque_nm` | 142 | Nm |
| Motor maximum torque | `motor_max_torque_nm` | 165 | Nm |
| Motor peak power | `motor_peak_power_w` | 35000 | W |
| SOC protection threshold | `soc_protection_threshold` | 0.30 | fraction |
| Gear ratio | `gear_ratio` | 1.00 | ratio |
| Final-drive ratio | `final_drive_ratio` | 3.94 | ratio |
| Driveline efficiency | `driveline_efficiency` | 0.90 | fraction |
| Motor efficiency | `motor_efficiency` | 0.92 | fraction |
| Inverter efficiency | `inverter_efficiency` | 0.95 | fraction |
| Auxiliary electrical load | `auxiliary_load_w` | 500 | W |
| Battery open-circuit voltage | `battery_open_circuit_voltage_v` | 350 | V |
| Battery internal resistance | `battery_internal_resistance_ohm` | 0.045 | ohm |
| Battery nominal energy | `battery_nominal_energy_wh` | 12000 | Wh |
| Numerical angular-speed epsilon | `omega_epsilon_rad_s` | 0.001 | rad/s |
| Numerical denominator epsilon | `numerical_epsilon` | 1e-6 | dimensionless |
| Default duration | `duration_s` | 30 | s |
| Default integration step | `time_step_s` | 0.01 | s |

Standard user inputs:

- `requested_torque_nm`: default 140; presets 60, 140, and 240 Nm; Phase-1 valid range 0 to 400 Nm.
- `motor_speed_rpm`: default 2500; recommended range 500 to 6000 rpm.
- `initial_soc`: default 0.70; valid range 0 to 1; recommended research range 0.30 to 0.80.

Advanced parameters may be editable behind an “Advanced” panel. A Reset button must restore the exact defaults above.

## 8. Exact Mathematical Logic

Use SI units internally. Preserve the equation numbering in code comments and technical documentation.

### 8.1 Torque-Regime Classification

Equation 5.1:

- If `T_req < 80 Nm`, `alpha_T = 1.00` and regime code is 1 (Low).
- If `80 <= T_req < 200 Nm`, `alpha_T = 0.50` and regime code is 2 (Medium).
- If `T_req >= 200 Nm`, `alpha_T = 0.50` and regime code is 3 (High).

The regime code is a research classification, not a diagnostic trouble code.

### 8.2 Motor Speed and Available Torque

Equation 5.8:

`omega_m = motor_speed_rpm * 2 * pi / 60`

Equation 5.2:

`T_m_limit = min(motor_max_torque_nm, motor_peak_power_w / (omega_m + omega_epsilon_rad_s))`

Equation 5.3:

`T_m_preliminary = alpha_T * T_req`

`T_m_feasible = clamp(T_m_preliminary, 0, T_m_limit)`

SOC protection:

- If current `SOC < soc_protection_threshold`, set `T_m = 0`.
- Otherwise set `T_m = T_m_feasible`.

### 8.3 Engine Torque and Clutch

Equation 5.4:

`T_e = clamp(T_req - T_m, 0, engine_max_torque_nm)`

Clutch state:

- If current `SOC < 0.30`, `u_c = 1` so the engine path is available.
- Else if `T_req < 80 Nm`, `u_c = 0` for the motor-first/electric-only baseline.
- Else `u_c = 1`.

### 8.4 P2 Wheel-Torque Conversion

Equation 5.5:

`T_w_req = T_req * gear_ratio * final_drive_ratio * driveline_efficiency`

Equation 5.6:

`T_w_act = (u_c * T_e + T_m) * gear_ratio * final_drive_ratio * driveline_efficiency`

Equation 5.7:

`torque_error_nm = T_w_req - T_w_act`

### 8.5 Motor and Battery Power

Equation 5.9:

`P_m = T_m * omega_m`

Equation 5.10:

`P_b = P_m / (motor_efficiency * inverter_efficiency) + auxiliary_load_w`

Phase 1 models propulsion discharge only. Reject negative requested torque instead of inventing regenerative logic.

### 8.6 Battery Current and Voltage

Equation 5.11:

`D = V_oc^2 - 4 * R_int * P_b`

Match the Simulink square-root protection:

`D_protected = clamp(D, 1e-9, 1e12)`

`I_b = (V_oc - sqrt(D_protected)) / (2 * R_int)`

Equation 5.12:

`V_t = V_oc - I_b * R_int`

Return an active-limit/warning message if `D < 0`, even though the protected calculation allows the simulation to remain numerically defined.

### 8.7 SOC

Equation 5.14:

`Q_n_as = (battery_nominal_energy_wh / V_oc) * 3600`

Equation 5.13:

`dSOC_dt = -I_b / Q_n_as`

At every time step:

`SOC_next = clamp(SOC_current + dSOC_dt * dt, 0, 1)`

Equation for display:

`SOC_percent = SOC * 100`

`delta_soc_percent = (initial_soc - SOC) * 100`

### 8.8 Loss, Energy, Efficiency, and Metrics

Equation 5.15:

`P_loss = I_b^2 * R_int`

Equation 5.16:

`E_b_Wh = integral(P_b dt) / 3600`

Equation 5.17:

`E_loss_Wh = integral(P_loss dt) / 3600`

Equation 5.18:

`battery_efficiency_percent = E_b_Wh / (E_b_Wh + E_loss_Wh + numerical_epsilon) * 100`

Equation 5.19:

`current_rms_a = sqrt(integral(I_b^2 dt) / max(elapsed_time, numerical_epsilon))`

Equation 5.20:

`torque_rmse_nm = sqrt(integral(torque_error_nm^2 dt) / max(elapsed_time, numerical_epsilon))`

Use a consistent numerical integration method. Trapezoidal integration is preferred. With constant inputs, results must match the baseline values below within tolerance.

## 9. Simulation-Core Design

Create a pure deterministic simulation core with no framework dependencies. Suggested responsibilities:

- `validate_inputs(request)`
- `classify_regime(torque, parameters)`
- `allocate_torque(torque, rpm, soc, parameters)`
- `calculate_driveline(...)`
- `calculate_motor_and_battery_power(...)`
- `calculate_battery_state(...)`
- `advance_state(state, dt, parameters)`
- `summarize_run(time_series, inputs, parameters)`
- `compare_runs(cases)`

Use typed request, parameter, time-series, and summary models. Keep formula code readable. Do not bury the equations inside UI components or route handlers.

Every result shall include:

- `model_id = "p2-full-parallel-torque-intensity"`
- `model_version`
- `formula_version = "simulink-parity-5.1-to-5.20"`
- input snapshot
- parameter snapshot
- start/end timestamps or deterministic run ID
- assumptions and limitations
- warnings and active limits

## 10. API Contract

Use the existing platform's API conventions. If none exist, implement:

### 10.1 Single Run

`POST /api/v1/hybrid/p2/simulate`

Example request:

```json
{
  "requested_torque_nm": 140,
  "motor_speed_rpm": 2500,
  "initial_soc": 0.70,
  "duration_s": 30,
  "time_step_s": 0.01,
  "parameter_overrides": {}
}
```

Response groups:

- `metadata`
- `inputs`
- `parameters`
- `summary`
- `active_limits`
- `warnings`
- `time_series`
- `scope_groups`

### 10.2 Comparison

`POST /api/v1/hybrid/p2/compare`

Accept two or more named cases and return aligned summary rows plus optional aligned time series. Provide preset cases:

- Low: 60 Nm, 2500 rpm, SOC 0.70.
- Medium: 140 Nm, 2500 rpm, SOC 0.70.
- High: 240 Nm, 2500 rpm, SOC 0.70.

### 10.3 Model Information

`GET /api/v1/hybrid/p2/model-info`

Return parameter definitions, units, allowed ranges, equations, scope groups, limitations, and version metadata so the interface does not duplicate hard-coded documentation.

## 11. Required Output Signals

Return these exact scientific signals with units:

1. `time_s`
2. `requested_torque_nm`
3. `engine_torque_nm`
4. `motor_torque_nm`
5. `motor_share_fraction`
6. `clutch_state`
7. `torque_regime_code`
8. `requested_wheel_torque_nm`
9. `actual_wheel_torque_nm`
10. `wheel_torque_error_nm`
11. `motor_speed_rad_s`
12. `motor_mechanical_power_w`
13. `battery_terminal_power_w`
14. `battery_current_a`
15. `battery_terminal_voltage_v`
16. `battery_internal_loss_power_w`
17. `soc_percent`
18. `delta_soc_percent`
19. `battery_energy_used_wh`
20. `battery_loss_energy_wh`
21. `battery_efficiency_percent`
22. `battery_current_rms_a`
23. `torque_rmse_nm`

Also support a compatibility CSV/export order matching `HybridResults`:

1. `T_req_Nm`
2. `T_engine_Nm`
3. `T_motor_Nm`
4. `T_wheel_requested_Nm`
5. `T_wheel_actual_Nm`
6. `SOC_percent`
7. `Battery_current_A`
8. `Battery_energy_Wh`
9. `Battery_loss_energy_Wh`
10. `Battery_efficiency_percent`
11. `Torque_RMSE_Nm`
12. `Torque_regime_code`

## 12. User Interface Requirements

The final platform must not expose only raw code or an API. Implement a complete responsive interface.

### 12.1 Main Controls

Provide:

- Low, Medium, and High preset buttons.
- Requested torque number field and slider.
- Motor speed number field and slider.
- Initial SOC number field and battery-style slider/gauge.
- Duration and time-step controls in Advanced settings.
- Expandable advanced parameter editor with units and reset-to-default.
- Run, Pause/Resume if supported, Reset, Compare, Save Session, and Export actions.
- Validation messages beside invalid fields.
- A visible statement that Phase 1 is a P2 constant-torque control-oriented model.

### 12.2 Live/Final Summary

Show at least:

- Regime and operating label.
- Engine torque.
- Motor torque.
- Requested and actual wheel torque.
- SOC and delta SOC.
- Battery current.
- Terminal voltage.
- Terminal power.
- Internal loss power.
- Battery energy used.
- Loss energy.
- Battery efficiency.
- RMS current.
- Torque RMSE.
- Active constraints/warnings.

Always display units.

### 12.3 Scope-Equivalent Charts

Provide the seven Simulink-equivalent chart groups below. Every chart must have a visible legend, axis labels, units, grid, tooltip, time cursor, zoom/reset, and accessible series labels.

1. **Torque Split**: Requested Torque, Engine Torque, Motor Torque.
2. **Mode and State**: Motor Share, Clutch State, Regime Code, Battery SOC.
3. **Wheel Torque Tracking**: Requested Wheel Torque, Actual Wheel Torque, Wheel Torque Error.
4. **Motor and Power**: Motor Torque, Motor Speed, Motor Mechanical Power, Battery Terminal Power.
5. **Battery Electrical**: Battery Terminal Power, Battery Current, Battery Terminal Voltage, Battery Internal Loss Power.
6. **Battery Energy and SOC**: Battery SOC, Delta SOC, Battery Energy Used, Battery Loss Energy, Battery Energy Efficiency, Battery Current RMS.
7. **Torque Error Metrics**: Wheel Torque Error, Running Torque RMSE.

Signals with substantially different units should use separate aligned axes/panels rather than unreadable scaling. Legends must remain visible. Do not remove a legend to reduce clutter.

### 12.4 Comparison View

Create a low/medium/high comparison page or panel with:

- aligned metric table;
- grouped bars for torque, power, current, energy, loss, efficiency, and delta SOC;
- overlaid SOC curves;
- clear case labels and legends;
- relative change indicators;
- export to CSV and JSON;
- a concise interpretation panel that states the observed trend without claiming physical validation beyond the model.

## 13. Required Visual Output and Animation

A full 3D moving car is not required for scientific validity and may imply vehicle-speed or road-motion dynamics that the Phase-1 model does not contain. The minimum required visual is a clear, animated technical power-flow view.

Implement a responsive 2D SVG powertrain visual containing:

`Battery -> Inverter -> Motor -> Transmission -> Final Drive -> Wheels`

and

`Engine -> Disconnect Clutch -> Motor/Transmission Input`

Visual behavior:

- Active energy/torque paths animate with directional arrows.
- Arrow thickness or pulse rate scales with torque or power.
- Engine is visibly inactive in the low-torque motor-first case.
- Clutch visibly changes between open and closed.
- Engine and motor contributions converge before the transmission in the P2 layout.
- Battery fill follows SOC.
- Motor/engine/wheel symbols rotate or pulse when active.
- Low, medium, high, and low-SOC operation are visually distinct.
- Labels show live torque/power values and units.
- A legend explains all visual states.

Optional enhancement:

- Add a car silhouette around the technical schematic or a lightweight 3D car view.
- Wheel rotation may be derived from `omega_wheel = omega_m / (gear_ratio * final_drive_ratio)` for animation only.
- Do not show travelled distance or scientifically labelled vehicle speed unless a wheel radius and longitudinal vehicle model are explicitly added as a future feature.
- Mark any road motion as illustrative, not as a validated vehicle-dynamics output.

Codex must deliver screenshots or captured browser evidence showing the final visual output for Low, Medium, and High cases. Backend-only completion is not acceptable.

## 14. Export and Session Requirements

Implement:

- CSV export with the 12-column compatibility order plus time.
- Full JSON export including inputs, parameters, assumptions, warnings, summaries, and time series.
- Chart image export if supported by the chart library.
- Printable result summary or report view.
- Session save/load using the existing platform storage approach; otherwise local storage for the prototype.
- A reproducible case name and run ID.

Do not save secrets or personal information in result files.

## 15. Scientific Regression Targets

For all three cases use:

- motor speed = 2500 rpm;
- initial SOC = 0.70;
- duration = 30 s;
- default parameters above.

Expected final values:

| Case | T_req Nm | T_m Nm | T_e Nm | T_w_req Nm | T_w_act Nm | P_b W | I_b A | V_t V | P_loss W | E_b Wh | E_loss Wh | Efficiency % | Delta SOC % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Low | 60 | 60 | 0 | 212.76 | 212.76 | 18472.50 | 53.142 | 347.609 | 127.082 | 153.937 | 1.059 | 99.317 | 1.292 |
| Medium | 140 | 70 | 70 | 496.44 | 496.44 | 21467.91 | 61.828 | 347.218 | 172.024 | 178.899 | 1.434 | 99.205 | 1.503 |
| High | 240 | 120 | 120 | 851.04 | 851.04 | 36445.00 | 105.561 | 345.250 | 501.443 | 303.708 | 4.179 | 98.643 | 2.566 |

Required tolerances unless the repository has stricter standards:

- Torque: plus/minus 0.02 Nm.
- Power: plus/minus 2 W.
- Current: plus/minus 0.02 A.
- Voltage: plus/minus 0.02 V.
- Energy: plus/minus 0.03 Wh.
- Efficiency: plus/minus 0.02 percentage points.
- Delta SOC: plus/minus 0.02 percentage points.
- Baseline torque RMSE: approximately zero within numerical tolerance.

## 16. Required Tests

At minimum, add and run:

1. Unit tests for every equation group.
2. Regression tests for the Low, Medium, and High baseline cases.
3. Low-SOC test: `T_req=60`, `initial_soc=0.25`; motor disabled, clutch closed, engine path active.
4. Motor power-limit test at high rpm.
5. Engine/motor saturation and non-zero torque-error test under excessive demand.
6. Invalid negative torque rejection.
7. SOC bounds and numerical-discriminant protection tests.
8. API schema and error-response tests.
9. Frontend form validation tests.
10. Chart-series and legend-presence tests where practical.
11. Comparison and export tests.
12. Responsive and accessibility checks.

Use deterministic fixtures. Do not weaken tolerances merely to pass tests.

## 17. Accessibility, Usability, and Performance

- Provide keyboard-operable controls and visible focus states.
- Do not communicate regime or warnings by color alone.
- Use high-contrast text, readable labels, and responsive layouts.
- Add tooltips for symbols and technical terms.
- Display units beside values and on chart axes.
- Preserve legends on every multi-series chart.
- Avoid blocking the UI during simulation; use a worker or asynchronous request if needed.
- Downsample chart display for long runs without changing the full exported data.
- Validate all numeric input on both client and server.

## 18. Integration Boundaries

Expose a stable simulation service so the wider platform can later supply or consume:

- battery power limits;
- motor torque/power limits;
- engine torque/fuel data;
- wheel-torque demand;
- vehicle-motion constraints;
- user/session metadata.

Keep future adapters separate from the validated Phase-1 equations. A future module must not alter baseline parity without a version change and new regression targets.

## 19. Documentation Required in the Repository

Create or update concise documentation covering:

- architecture and folder layout;
- setup and run commands;
- formulas and parameter units;
- API examples;
- UI use;
- screenshots;
- baseline validation table;
- assumptions and limitations;
- extension points;
- test commands and results.

Keep scientific logic documented close to the implementation. Do not rely only on this `AGENTS.md` after the application is built.

## 20. Definition of Done

The work is complete only when all conditions below are met:

- The existing platform contains a working P2 hybrid module.
- MATLAB is not required to run it.
- The mathematical core matches Equations 5.1-5.20 and the three regression cases.
- Users can change torque, rpm, SOC, duration, and approved parameters without editing code.
- All seven scope-equivalent chart groups are present with visible legends.
- The animated power-flow schematic responds correctly to model states.
- Low, Medium, High, low-SOC, and saturation cases have been tested.
- Comparison and export work.
- Input validation and error messages work.
- Automated tests, type checks, lint, and builds pass.
- The application has been opened in a real browser and visually inspected.
- Codex provides screenshots for Low, Medium, and High cases, including the animated power-flow view and charts.
- Documentation states the model boundary and does not claim production-vehicle validation.

## 21. Required Codex Final Report

At the end of implementation, report:

1. Existing stack discovered and architecture used.
2. Files created or modified.
3. Exact simulation logic location.
4. API routes and UI route.
5. Commands to install, run, test, lint, and build.
6. Automated test results.
7. Baseline numerical comparison against all three expected cases.
8. Browser validation performed.
9. Links or paths to Low, Medium, and High screenshots.
10. Export examples.
11. Remaining limitations and clearly separated future extensions.

Do not conclude with “code generated” alone. Demonstrate that the platform runs and that the corresponding visual output is present and scientifically aligned with the delivered model.
