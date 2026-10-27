# BrakeLab integration

Regenerative and Friction Brake-Force Allocation is the configured BEV model.
Fuel Delivery Optimisation remains under ICE; Engine Live Data stays withdrawn.
Use the existing system selector, enter BEV, and open BrakeLab at
`/virtual-lab/brakelab/` (`core:brakelab`). Active Administrator, Lecturer and
Student access checks are unchanged. No migration, hardware connection, external
service, secret, public API or additional runtime dependency was added.

## Sources and verification boundary

On 27 October 2026 the project owner explicitly authorised implementation and
deployment from the two programmer files already provided, without waiting for
`BrakeModel.slx` or `BrakeModel_Guide.docx`:

- `Codex_BrakeLab_Prompt.md`, SHA-256
  `edad7cc5799d9e4dea212ff19f2c0126182cffbae49143022d10719d62e731ba`.
- `BrakeLab_Programmer_Guide.docx`, SHA-256
  `2cd4f26ecaca3b607cf25f1f77a74dc79cc359b14ef2349a5f0c547a6ac1199f`.

The complete prompt, all eight rendered guide pages, tables and figure were
reviewed. The guide's shared conversation and earlier linked-source audit remain
provenance, not a reason to restore superseded full-vehicle scope. The detailed
prompt's canonical reference supplies explicit W/kW conversion factors omitted
from some condensed Word equations.

This is verification against the supplied canonical programming reference and
acceptance table. The missing SLX has not been inspected or run; no MATLAB
solver equivalence, measured vehicle validation or brake-controller certification
is claimed. The interface and JSON source-basis field disclose this limitation.

## Implementation and plain-data interface

The stack is existing Django templates, vendored Bootstrap and local ES modules.
`static/js/brakelab/model.mjs` exports the deterministic
`calculateBrakeAllocation(inputs, calibration?)` function, 11 approved inputs,
all 25 engineering numerical outputs, active-limit code/label, warnings and six
visual aids. Names and units follow the prompt. Core calculations require no DOM,
database, MATLAB, frontend framework or internet after assets load.

`static/js/brakelab/controller.mjs` owns each page's operating point and separate
screen playback. `ui.mjs` updates cards, charts, explanations and the original SVG
in `templates/core/brakelab.html`. Input editing helpers and workbench styles
are reused from Fuel Delivery without coupling the two calculation engines or
sharing simulation state. `static/css/brakelab.css` adds the BEV accent and charts.

JSON export includes module id/version, raw inputs, fixed calibration, the
canonical result, force-balance status, illustrative-playback metadata and source
basis. It is local learning evidence, not an assessment submission, private
integration token or hardware command. Exported results are copies, not references
to mutable controller state. A future orchestrator can call the pure function
directly with ordinary JSON-compatible data; no new integration framework exists.

## Validation and explicit source decisions

Ten numeric inputs must be finite. Mass and voltage must be positive; the four
component limits may be zero but not negative. Recommended ranges warn rather
than prohibit deliberate finite out-of-range engineering values. Numeric entry,
soft-range sliders and touch/keyboard nudges stay synchronised; numeric values
outside the slider's broad rendering scale disable that slider with explanatory
accessible text. Derived non-finite calculations are errors, never JSON nulls.

The UI enable control is boolean. The reusable function also preserves the
canonical reference's finite numeric enable-factor extension, clamped to 0–1.
NaN, infinity, strings and missing enable values are rejected. Out-of-range
numeric enable values warn. Raw brake demand and SOC are normalised to 0–1 and
0–100%; negative speed is calculated as zero. Warnings disclose normalisation
without replacing the saved raw inputs.

All 15 calibration values remain in one frozen default object. The collapsed
Advanced calibration panel is read-only, avoiding accidental unreviewed changes.
Programmatic custom calibration must have finite values, positive mechanical
scales/deceleration/minimum speed/epsilon, efficiencies in (0,1], and ordered
speed, SOC and temperature thresholds. These guards supplement the reference's
incomplete invalid-calibration checks without changing valid default equations.

Candidate ties retain canonical stable order: demand, torque, motor power,
battery. Battery diagnostics retain SOC/temperature/current/power refinement and
priority. Separate factor gauges expose simultaneous restrictions rather than
pretending the single active code is a complete diagnosis of every constraint.

For requested force below 1 N, the source's protected percentage denominator is
retained: shares need not sum to 100%, and `NO_BRAKING` also covers that region.
The chart does not silently renormalise those shares, and explanatory text makes
the diagnostic threshold explicit. At zero demand with nonzero speed, the
reference's zero stop-time/distance values are sentinels: the UI says no finite
stopping estimate and does not depict an instantaneous stop.

## Interaction and visual contract

All 11 inputs have units and simple parameter-purpose explanations connected to
their controls. Numeric help uses keyboard/touch-accessible disclosures.
Live Update previews is on by default. Editing always stops playback; with live
preview off it marks the draft stale and blocks export until Run Model. Invalid
input/calculation errors also block Run/export while labelling last-valid readings.
Reset to Baseline restores the approved inputs and clears stale playback/results.

The nine main cards and expandable calculation details show all required numeric
fields; the force-balance residual is prominent, with an explicit <0.001 N check.
Force/torque use one decimal, power/current two, factors three and shares one.
The residual uses scientific notation to preserve the meaning of its tolerance.
The active-limit banner and explanation use actual candidate forces/factors.

Four graphical groups are present:

1. Solid/striped regenerative/friction allocation, with text values.
2. Demand/torque/power/battery force bars, with the smallest candidate labelled.
3. Separate speed/SOC/temperature factor indicators.
4. Mechanical regenerative, allowed battery and actual battery power bars.

The original SVG shows a side-view BEV, rotating wheels, wheel-to-motor and
motor-to-battery flow, and friction-disc glow. Run Model starts from the entered
speed, uses the reference stop-time and 1–8 s scaled playback duration, and ends
at zero illustrated speed. Wheel angle is proportional to illustrated distance
with explicit visual compression. Flow intensity uses the supplied regeneration
and battery-charge intensity fields; glow uses the friction-share intensity,
not a claimed disc temperature. A low-speed visual fade suppresses arrows as
illustrated speed falls; all recovery flow stops at zero speed.

Operating-point outputs stay fixed during playback. No allocation time-series,
dynamic SOC, recovered kWh, battery heating, road load, wheel slip, ABS/ESC or
stopping-performance validation is invented. Constant-deceleration estimates and
scaled screen motion are clearly labelled. Pause/Resume, background pause,
motion-off and changing reduced-motion preference are supported. Opening a new
page starts a fresh baseline preview, not another user's or module's state.

## Baseline and verification

At the approved baseline: deceleration 1.4 m/s², demand 2100 N, wheel torque
651 N·m, motor speed 4620.627 rpm (about 4621), torque limit 4807.742 N,
motor-power limit 3000 N, battery limit 2863.636 N, regenerative force 2100 N
and friction 0 N. Mechanical power is 35 kW, charging 30.8 kW and 88 A;
shares 100%/0%, residual 0 N, limit Driver demand. Estimated stop time
11.904762 s and distance 99.206349 m produce 8 s screen playback.
These are computed, not hard-coded UI values.

`tests/brakelab/source-contract.json` preserves the exact canonical TypeScript
reference and source hash. Its dev-only esbuild transformation allows numerical
comparison without adding TypeScript or Node to the deployed calculation runtime.
2500 seeded operating points compare every numerical/visual field and final
limit diagnostic, in addition to baseline, boundaries, zero limits, normalisation,
fractional enable, calibration validation, overflow, ties and playback tests.
The tests do not claim to substitute for a future SLX or physical-engine check.

```sh
.venv/bin/python manage.py runserver
node --test tests/brakelab/model.test.mjs tests/fuel_delivery/model.test.mjs
.venv/bin/pytest -q
ATU_BROWSER_CHANNEL=chrome .venv/bin/pytest -m e2e tests/e2e/test_brakelab_ui.py tests/e2e/test_fuel_delivery_ui.py tests/e2e/test_laboratory_flow.py -q
```

Isolated browser tests cover values, charts, export, scaled stopping, flow
suppression, limits, live/stale drafts, zero/near-zero demand, errors, fresh
navigation, reduced-motion changes, keyboard/touch controls, responsive layout
and axe checks at desktop/mobile widths. Screenshots are generated under
`test-results/brakelab/`; deployment health and live smoke checks are separate.
