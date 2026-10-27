# Fuel Delivery Optimisation integration

Fuel Delivery Optimisation is currently the only active model under ICE.
It was originally added as the second model without changing Engine Live Data
Demonstration. That module was subsequently withdrawn on 26 October 2026;
its source and assets are retained but its catalogue entry and route are removed.
The withdrawal does not change Fuel Delivery Optimisation's inputs, equations,
visualisation, controls or exports.

## Entry and access

Sign in, choose Virtual laboratory, enter ICE, then select Fuel Delivery
Optimisation. The authenticated route is
`/virtual-lab/fuel-delivery-optimisation/` (`core:fuel_delivery`). Existing
active Administrator, Lecturer and Student checks apply, including forced
password change and suspension. There is no new service, dependency, data
migration, hardware connection, public simulation API or account credential.

The pure browser ES module is the calculation source of truth, consistent with
the existing platform. Model runtime needs neither MATLAB nor internet access
after the page's local files have loaded. It is not a newly hosted offline app.
No global simulation state, telemetry or third-party generation request is used.

## Interactive 3D visualisation

The locally bundled Three.js scene is a generic teaching assembly, not a measured CAD model. The displayed fuel flow, injector pulse width and duty use the same current calculation as the KPI cards. A deliberately slowed representative pulse uses duty and the calculated dead-time fraction; the fuel path, droplets, cylinder, piston position and spray shape are illustrative. The source model does not calculate tank depletion, pump dynamics, crank angle or spray physics. Component buttons point the camera at each part and explain it; orbit, zoom and reset are available. A labelled 2D schematic is retained as a user-selectable view and automatic WebGL fallback. Reduced-motion settings turn off illustrative playback by default. `node scripts/sync_assets.mjs` rebuilds the locally served 3D bundle from `frontend/fuel-delivery-3d.mjs` and the pinned Three.js package.

The vehicle-context perspective uses the shared GV70 project baseline for overall length, width and height, wheelbase, front and rear track and tyre radius, directly from the server-provided baseline. The stylised body outline, component positions and routing are illustrative and do not represent verified GV70 geometry. The separate injector cutaway is enlarged and not to scale. This visual reference does not change the fuel calculation, its inputs or its original source assumptions.

For axle placement the view also uses the 2025 Australian GV70 specification's 0.845 m front and 0.995 m rear overhangs ([Genesis specification](https://www.genesis.com/content/dam/genesis/au/en/documents/2006650_GV70%2BMY25%2BModel%2BLaunch_v0.3.pdf)). These additional visual dimensions are not simulation inputs; configurations can differ by market and model year.

## Sources and source audit

Supplied on 26 October 2026:

- `CODEX_Fuel_Delivery_Virtual_Platform_Implementation_Script.md` (979 lines).
- `Fuel_Delivery_Virtual_Platform_Programmer_Guide.docx`.
- `Fuel_Delivery_Optimisation_All_In_One.slx`.

The separate Data and Use Guide was unavailable at the initial implementation.
It was subsequently supplied in `Downloads/Fuel Delivery Module` and audited on
26 October 2026, together with both programmer documents, all rendered guide
pages/figures, the actual SLX, and the Programmer Guide's embedded shared-chat
link. Its SHA-256 is
`d0ee8755259d08337cfda7e009235d1ce78f84af9d4019bd98563899f9069859`.
The later source confirms the current defaults/ranges, parameter purposes,
gain-zero behaviour and educational boundaries. Historical ignition scope was
superseded by fuel-delivery scope; it has not been restored. Inaccessible linked
papers are not claimed as fully reviewed or as physical validation.

No MATLAB numerical run has been performed, so this is verification against the
supplied equations, wiring and rounded acceptance table, not solver-to-solver
validation. Constant-input analytic checks show convergence as the web time step
is reduced; these are not MATLAB runs or real-engine measurements.

The SLX SHA-256 is
`655656079f3411e887056eac1bdf68978f3d4da28ac2861b2b31cd16224fa492`.
Its saved solver is `VariableStepAuto`, with stop time 30 s. The web implementation
uses the deterministic step convention requested by the programmer script:
update LTFT, evaluate delivery, then integrate cumulative fuel using that step's
flow. Default step is 0.1 s; a partial final step ends exactly at the duration.
Convergence against the continuous Simulink solver remains a separate check.

`scripts/inspect_fuel_slx.py` reads the ZIP/XML without executing model content.
`tests/fuel_delivery/source-contract.json` preserves the extracted mathematical
blocks, connections, input defaults and solver settings for reproducible CI.
The independent test evaluator traverses those block expressions/connections,
then checks all eight output-vector positions against the implementation across
all seven presets. The source archive itself is not required at runtime or CI.

Two differences from the Markdown reference were resolved in favour of the SLX:

- LTFT: block 516 is an unrestricted integrator followed by block 517's output
  limit of -20 to +20%. The web state retains `ltftIntegralPct` as well as the
  saturated `ltftPct`; it does not silently implement anti-windup. This affects
  reversal after prolonged saturation, but not the default case.
- BSFC: block 720 limits its power denominator to 0.1–1,000,000 kW. The
  Markdown only specified a lower limit. The SLX upper limit is preserved.

The guide sentence about “closing” feedback setting STFT to zero is interpreted
using the equations and wiring: disabling closed loop sets STFT to zero and
stops further learning; previously learned LTFT remains until a new run/reset.

## Controls and visual behaviour

All 15 model inputs and the duration/step settings have units, numeric editors,
keyboard sliders and touch-sized minus/plus buttons. Seven editable presets
start from defaults. Out-of-classroom-range inputs show warnings without silently
altering the equations. Non-finite or unsafe denominator inputs are errors.
Every input has purpose help; numeric explanations use keyboard/touch-accessible
disclosures. Soft-range sliders expand to represent typed values, and nudges
retain their step outside classroom guidance instead of snapping to a boundary.
The optimisation scale is explicitly bounded to 0.85–1.05, duration to 5–120 s
and step to 0.02–1 s, bounding each run to 6,000 full-size steps.

Run new clears state/history. Pause and Resume retain them. Edits pause the
run and recalculate without advancing time. History retains each sample's
own inputs, including edits during a paused run. Reset restores all defaults.
An edit that makes duration shorter than recorded elapsed time is rejected,
with a field-specific message to Reset before selecting a shorter run. The
recorded time/settings/history remain unchanged, and exports are blocked until
the invalid draft is corrected or Reset. This prevents a 30-second result from
being relabelled as a five-second run.
Backgrounding/navigation pauses time. Reduced motion disables illustrative
animation by default and honours preference changes.

Calculation errors during stepping or comparison stop playback, invalidate the
controller status, preserve last-valid readings/history and display a clear error.
Resume/comparison/exports are blocked until correction or Reset. Controller
`payload()` and `csv()` also reject stale evidence after a calculation failure.
Non-finite outputs and non-positive computed fuel/flow (including numerical
underflow) are explicit errors, not silently corrected source equations.

The responsive SVG fuel path shows source, rail, injector and cylinder. Buttons
explain each component. Flow thickness follows calculated g/s; injector/spray
width follows calculated pulse width; opening cadence follows RPM with an
explicit illustrative compression of at most 1.5 cycles/s. A smooth, non-strobing
pulse changes opening/spray opacity; the cylinder also has a restrained
injection-event highlight. Pausing stops it.
Disabling motion, Pause and reduced-motion preference changes return the event
cue to its static state. Mixture colour reflects
predicted lambda relative to target (0.03 tolerance), with text labels as well.
Duty and cumulative-fuel progress meters show numeric values and explicit
scales. The duty gauge has normal (≤85%), high (>85%) and saturated (100%) states,
distinct visual accents, a text caption and accessible value text; warnings do
not depend on colour alone. These are not validated geometry, spray, combustion
or tank-level models.
No vehicle speed or vehicle movement is invented from RPM.

Six labelled SVG charts show target/measured/predicted lambda, trims, flow,
cumulative fuel, pulse width and duty. Different units have separate plots.
Charts decimate display points only; JSON/CSV keep every full-resolution sample.
The table and bars compare fresh full-duration baseline and adjusted runs with
identical current inputs except the optimisation scale. This is not a replay
of an edited run. Editing/reset/new run invalidates a previous comparison.
Compare, Apply recommended scale and JSON/CSV exports are in the top toolbar,
with an analysis jump link. Learning help explains the nominal gasoline 14.7:1
mass ratio and that zero learning gain freezes LTFT without disabling STFT.

Saturation, >85% duty, out-of-band lambda, savings off target and meaningless
near-zero-power BSFC remain explicit. The compatibility vector keeps finite
protected BSFC while the UI says it is not meaningful. Requested duty before
limiting is available in Calculation details. Fuel delivery remains theoretical
when the injector saturates; no post-hoc physics correction changes the source.

## Exports and platform contract

JSON includes `moduleId`, `moduleVersion`, simulation time/settings, inputs,
named outputs, status/warnings, full history and optional fresh-run comparison.
The exact legacy vector order is:

1. Final fuel mass in mg/event
2. Injector pulse width in ms
3. Injector duty cycle in %
4. Predicted lambda
5. Fuel flow in g/s
6. Cumulative fuel in g
7. BSFC in g/kWh
8. Fuel saving in %

CSV has simulation time, per-sample inputs and named outputs. Invalid drafts
cannot export stale results. JSON/CSV are local learning evidence, following
the existing engine export pattern. No assessment is auto-submitted and no
unsigned browser payload is accepted as a signed external-resource callback.
The existing short-lived signed-return assessment workflow remains unchanged.

The hardening revision is `moduleVersion: 1.0.1`; names, units, equations and
legacy vector order are unchanged. JSDoc explicitly describes all 17 inputs,
state, 27 outputs, eight-element vector, status and platform payload. The pure
`evaluate()` result contains sibling `state`, `outputs`, `integrationVector` and
`status` fields. Controller `payload()` puts the vector at top level beside
named outputs as in the preferred platform JSON, not nested inside outputs as
in the illustrative Markdown TypeScript example. Source correction coefficients
and educational warning thresholds are named separately.

## Hyper3D assessment

Hyper3D's official documentation describes text/image-to-3D asset generation,
not an engineering simulation engine. Generation APIs require a bearer key
and credit-based usage. No key, purchase, subscription, uploaded project file
or credit-consuming generation was requested or performed here. The module
therefore ships a code-native interactive SVG schematic, as the supplied
specification recommends, with no external dependency. No AI mesh is claimed.
A later licensed GLB can be added as a visual asset, but must still be wired
to this deterministic model and labelled as illustrative geometry.

Official references inspected on 26 October 2026:

- https://docs.hyper3d.ai/en/get-started/quick-start
- https://hyper3d.ai/features/api

## Verification and running locally

```sh
.venv/bin/python manage.py runserver
node --test tests/fuel_delivery/*.test.mjs
.venv/bin/pytest -q
ATU_BROWSER_CHANNEL=chrome .venv/bin/pytest -m e2e tests/e2e/test_fuel_delivery_ui.py tests/e2e/test_laboratory_flow.py -q
.venv/bin/python scripts/inspect_fuel_slx.py /absolute/path/Fuel_Delivery_Optimisation_All_In_One.slx
```

Default 30-second outputs (rounded to three decimals): base/final fuel 20.408
mg/event; pulse 8.471 ms; duty 17.648%; lambda 1.000; STFT/LTFT 0.000%; flow
1.701 g/s and 8.218 L/h; cumulative fuel 51.020 g; brake power 20.944 kW;
BSFC 292.325 g/kWh; saving 0.000%; recommended scale 1.000.
