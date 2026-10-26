# Fuel Delivery Optimisation integration

Fuel Delivery Optimisation is the second model under ICE. Engine Live Data
Demonstration and its calculation, controller, template, 3D assets and tests
are not changed by this addition.

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

## Sources and source audit

Supplied on 26 October 2026:

- `CODEX_Fuel_Delivery_Virtual_Platform_Implementation_Script.md` (979 lines).
- `Fuel_Delivery_Virtual_Platform_Programmer_Guide.docx`.
- `Fuel_Delivery_Optimisation_All_In_One.slx`.

The separate Data and Use Guide was not supplied. No MATLAB numerical run has
been performed, so this is verification against the supplied equations, wiring
and rounded acceptance table, not a claim of solver-to-solver validation.

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
The optimisation scale is explicitly bounded to 0.85–1.05, duration to 5–120 s
and step to 0.02–1 s, bounding each run to 6,000 full-size steps.

Run new clears state/history. Pause and Resume retain them. Edits pause the
run and recalculate without advancing time. History retains each sample's
own inputs, including edits during a paused run. Reset restores all defaults.
Backgrounding/navigation pauses time. Reduced motion disables illustrative
animation by default and honours preference changes.

The responsive SVG fuel path shows source, rail, injector and cylinder. Buttons
explain each component. Flow thickness follows calculated g/s; injector/spray
width follows calculated pulse width; opening cadence follows RPM with an
explicit illustrative compression of at most 1.5 cycles/s. A smooth, non-strobing
pulse changes opening/spray opacity. Pausing stops it. Mixture colour reflects
predicted lambda relative to target (0.03 tolerance), with text labels as well.
Duty and cumulative-fuel progress meters show numeric values and explicit
scales. These are not validated geometry, spray, combustion or tank-level models.
No vehicle speed or vehicle movement is invented from RPM.

Six labelled SVG charts show target/measured/predicted lambda, trims, flow,
cumulative fuel, pulse width and duty. Different units have separate plots.
Charts decimate display points only; JSON/CSV keep every full-resolution sample.
The table and bars compare fresh full-duration baseline and adjusted runs with
identical current inputs except the optimisation scale. This is not a replay
of an edited run. Editing/reset/new run invalidates a previous comparison.

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
