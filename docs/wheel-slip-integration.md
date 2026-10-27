# Wheel-Slip ABS/TCS integration

The Vehicle Dynamics catalogue contains the role-protected Wheel-Slip Control Using ABS and TCS module at `/virtual-lab/vehicle-dynamics/wheel-slip-abs-tcs/`. It is an educational longitudinal model, not a production controller, hardware interface, or safety validation.

## Source and scientific boundary

The numerical implementation follows the equations and thresholds in the supplied `CODEX_WheelSlip_ABS_TCS_Virtual_Platform_Task.md` and the accompanying `WheelSlip_ABS_TCS_Programmer_Guide.docx`. The guide's linked shared chat was inspected and describes the five scopes and the intended model. Its final model download reported “Failed to get upload status”; `WheelSlip_ABS_TCS_Final.slx` was also not found in the searched project and Downloads paths. The implementation has **not** been compared with that Simulink model, MATLAB, or a real vehicle.

The written wheel acceleration uses `(driveTorque - brakeTorque - tyreForce * radius) / inertia`. It is implemented as written; the underlying sign convention and dynamics need confirmation against the missing model. The model represents one wheel, four equal tyre loads, no lateral/load-transfer dynamics, and no hydraulic actuators. The interface shows these limits.

## Contract and behaviour

`static/js/wheel-slip/model.mjs` exports `DEFAULTS`, `FIELDS`, `PRESETS`, `validateConfig`, and the pure synchronous `simulate(config)` function. A module worker calls it so computation is separate from the interface. The 16 configurable numeric/Boolean fields plus fixed `timeStepS=0.001` are specified in the source task. Input ranges are enforced, including step times no later than duration and duration aligned to a 1 ms step.

The returned object contains `config`, `modelVersion`, `warnings`, full-resolution `samples`, and `metrics`. Each sample has time, vehicle and wheel speeds, brake and drive slip, applied torques, per-wheel tyre force, controller mode and flags, distance, and integrated wheel angle for playback. Euler updates use the pre-step slip and force, and sample the resulting state at the end of the step. Stopping is the first recorded sample at or below 0.1 km/h, including an initially stationary vehicle. ABS/TCS active time includes apply, hold, and release/reduce modes, as required by the supplied flags.

Playback is an illustrative SVG driven by recorded distance and wheel angle, with controller labels and lock/spin cues. Six SVG charts show speed, slip, torque, per-wheel force, controller timeline and distance, with hover readings, zoom around playback position and SVG download. Per-bin extrema and controller transitions are retained in chart display; complete samples remain in JSON and CSV. CSV begins with comment rows recording model version and configuration.

Presets populate controls but never start a run. Editing inputs invalidates the prior run and disables export; reset clears state and terminates any running worker. Simulation output exports are local learning evidence, consistent with the existing demonstration modules; they do not create an assessment submission. The platform's practical submission flow requires a separately configured task/resource and is not automatically invoked by this module.

## Verification

Run numerical checks with `node --test tests/wheel_slip/model.test.mjs`; run platform checks with `.venv/bin/pytest -q`. Browser tests are in `tests/e2e/test_wheel_slip_ui.py`, using the repository's existing pytest/Playwright setup. Run the platform locally with `.venv/bin/python manage.py runserver`.
