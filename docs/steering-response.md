# Vehicle Steering Response

Implementation plan: reuse Django role-protected pages, the Vehicle Dynamics catalogue, browser ES modules, worker calculation, SVG plots and the shared walkthrough. Keep the supplied five-state bicycle equations in one pure RK4 engine. Use the same samples for all eleven outputs, trajectory replay and CSV/JSON exports. Verify the supplied reference, zero-steering symmetry, mass/speed protections and numerical limits; then check responsive layout, accessibility and deployment.

Source: the uploaded `AGENTS.md` is treated as this module's implementation specification, alongside `Vehicle_Steering_Response_Virtual_Platform_Programmer_Guide.docx`. It is retained under `docs/reference/steering-response/` rather than installed as unrelated repository-wide agent policy. The named `Vehicle_Steering_Response_Organized_All_in_One_With_Legends.slx` was not present locally at initial inspection.

## Source review and scientific scope

The guide's tables, equations, architecture diagram and dashboard figure were inspected. The [linked shared conversation](https://chatgpt.com/share/6adcf7b2-4a50-83e9-8a40-829ee976507b) was readable and confirms the eleven-signal Mux and four labelled scope groups. Its model download returned “Failed to get upload status” for the named SLX; the data-guide download did not yield a locally available file. No MATLAB simulation or inspection of the original SLX has been performed. Verification is against the complete written equations, reference engine and acceptance values.

The model has five zero-initialised states: beta, yaw rate, heading, X and Y. Speed is constant. Axles use linear cornering stiffness; no tyre saturation, roll, pitch, suspension, load transfer, steering-assist dynamics or braking/stability controller is added. Positive yaw is displayed as counterclockwise in the global X-Y plane; SVG screen Y is inverted for presentation only. The model uses the exact supplied turning-radius epsilon 0.001.

## Implementation and interface

- Authenticated page: `/virtual-lab/vehicle-dynamics/steering-response/` (`core:steering_response`), listed under Vehicle Dynamics.
- `static/js/steering-response/model.mjs`: pure deterministic `simulateSteeringResponse(vehicle, scenario)`, validation, profile generator, defaults, output order and CSV adapter. JSDoc describes input contracts.
- `worker.mjs`: calculation worker; UI edits/cancellation terminate outstanding work.
- `ui.mjs`, `charts.mjs`, `trajectory.mjs`: inputs, replay, four plot groups, ten independently scaled chart panels and the top-down trajectory marker.
- `OUTPUT_VECTOR_ORDER` and `platformVector(sample)`: exact eleven-signal contract. Results expose the final named sample as `final`, ordered final vector as `platformVector`, timestamped `samples`, original `parameters`, `scenario`, warnings, effective protections and solver metadata. CSV and JSON use the same sample array as charts and replay.

No new simulation API, persistence service or runtime language is introduced. The established platform runs pure browser modules. CSV/JSON exports are local learning evidence and do not create an assessment submission. Presets support reference step, zero-steering, sine, doublet and explicitly changed common-baseline mass/wheelbase.

## Numerical and resource safeguards

The reference case uses fixed RK4 at 0.01 s and one internal step per output interval. Low-speed and extreme research parameters can produce a stiff lateral subsystem, for which the reference output interval would be unstable. The implementation deterministically subdivides each interval using a conservative lateral-state matrix norm. Equal internal subdivisions, their count and the unchanged output interval are disclosed in result metadata and warnings; the reference equations and default result are unchanged. At most 120,001 output samples and 2,000,000 internal RK4 steps are permitted. Requests exceeding these limits are rejected with an explanation rather than silently truncated. A partial final output interval ends exactly at the requested duration. Non-finite results fail without exposing stale exports.

Inputs outside slider suggestions remain editable when they satisfy the stated validation rules. The reference protections U ≥ 0.5 m/s and 100 ≤ m ≤ 50,000 kg are applied with warnings. A too-large steering/sideslip/lateral-acceleration result prompts a linear-model interpretation warning. These are educational checks, not physical validation.

## Common vehicle baseline

The approved steering reference remains 1,500 kg, a = 1.2 m and b = 1.6 m (2.8 m wheelbase). The shared-baseline preset explicitly changes base mass to 2,000 kg and a+b to 2.875 m, retaining a:b as an assumed distribution. Inertia and stiffness remain independent assumptions, not measured GV70 calibration. The marker uses shared vehicle body proportions; its screen size is fixed for visibility while its position, heading and wheel angles follow recorded outputs. The trajectory axes use equal spatial scale. No physical body roll or suspension animation is inferred.

## Verification and usage

Start the project normally with `.venv/bin/python manage.py runserver`, sign in, enter Vehicle Dynamics and open Vehicle Steering Response. Select Run simulation, then inspect the final sample or use replay/scrubbing. Reduced-motion mode offers the static trajectory and manual position slider without animated playback.

Run:

```sh
node --test tests/steering_response/*.test.mjs
.venv/bin/pytest tests/test_steering_response.py -q
.venv/bin/pytest -m e2e tests/e2e/test_steering_response_ui.py -q
```

The 10 s reference produces yaw rate 4.70272086 deg/s, sideslip −0.17836748 deg, lateral acceleration 1.36796605 m/s² (0.13944608 g), radius 200.61477320 m, heading 41.87612118 deg, X 153.96269431 m, Y 51.46509589 m, front force 1172.54232583 N, rear force 879.40674437 N and steering-wheel angle 16 deg. All agree with the supplied rounded acceptance table within its tolerances.

Visual evidence is stored under `test-results/steering-response/` using the project's ignored test-artifact convention: full-interface, final-trajectory and steering-event screenshots at desktop and mobile widths.
