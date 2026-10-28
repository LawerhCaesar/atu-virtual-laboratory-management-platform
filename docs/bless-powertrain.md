# Bless fuel-cell / battery and diesel comparison

Registered under FCEV at `/virtual-lab/fcev/fuel-cell-battery-diesel/`. Approved administrator, lecturer and student accounts use the existing login/access controls. Computation is local to a module Web Worker; no MATLAB service, database migration, payment service or extra runtime dependency is needed.

## Source and conversion

The supplied Python handoff was inspected before execution, then its SHA-256-checked archive was extracted into `docs/reference/bless-battery/`. The original SLX, R2024b graph, both guides, parameter/output catalogs, ten scenario specifications and forty native time histories remain there. They are development references, **not browser assets**. The script's original `validate-results` checker passed all 40 generated streams with its unchanged tolerance and matching model/input metadata. The complete report is `docs/reference/bless-battery/browser-parity-report.json`.

`compile_model.py` checks the three source JSON hashes, resolves local From/Goto tags and hierarchical ports, detects combinational cycles, and generates a dependency-ordered static graph. A build-time expression parser preserves operators (including power), one-based vector indexing, numeric logicals and parentheses. Neither user settings nor imported files are evaluated as code. All 2,063 blocks have path/SID entries in `conversion-map.json`: 697 numerical nodes, scoped wiring and presentation-only elements. All 302 Fcn expressions, 17 UnitDelay states and 106 channels are accounted for. State inputs are committed simultaneously after sampling; t=0 is retained. No generic integrator replaces the delayed recurrences.

The OCV table uses linear point-slope interpolation and clipped extrapolation. Battery initialization retains the trapezoidal OCV inventory integral; the pack kWh scale is applied once, matching the native inventory gain. This floating-point evaluation order matters at zero commanded distance because the native guarded per-distance output magnifies one-ULP differences. No scenario-specific constants, lookup traces, adjusted tolerance or zero-distance special case were added to the engine.

`engine.ts` exposes typed scenario, simulation, sample and result boundaries. `engine.mjs` is its reproducible esbuild output; `graph.mjs` and `catalog.mjs` are the graph compiler outputs. State indices map to the ordered UnitDelay entries in the source parameter catalog and conversion map. Public API: `validateScenario`, `createSimulation`, `stepSimulation`, `runScenario`, `toDisplaySample`, scenario import/export, native result CSV and full result JSON. The simulation owns a copied input snapshot. Unknown versions, malformed arrays and nonfinite values are rejected. Browser limits of 14,400 seconds, 50 kB imported scenarios and numeric magnitude 1e9 are resource/form limits, not validated physical operating ranges. Native operating clamps are reported without replacing the saved raw inputs.

## UI and interpretation

The default view exposes driving, environment, storage and price settings. All remaining component settings and the 18 battery mask entries are editable in Advanced. Ten supplied examples are available; example prices are explicitly illustrative. Inputs can be saved per account/browser or exported/imported. Edits pause playback, cancel an in-flight calculation and mark completed results stale until recalculated. Cancellation terminates the worker; run IDs reject stale messages. Reset clears output. Page hiding pauses playback.

Every card, table, chart cursor and animation uses the same completed run and integer sample. Playback never changes the numerical one-second clock. Vehicle/road motion is illustrative requested-speed playback; it is not achieved motion. Fuel-cell chemical/module/DC flow, battery DC direction and accepted regeneration map to the named native outputs. Motor AC and inverter DC channels are explicitly labelled **demand** and do not animate as guaranteed delivered flow; the graph has no separately validated actual motor-power solution for a DC shortfall. Auxiliary demand is likewise labelled. Battery/converter and boost losses are separate. Motion can be disabled manually and respects reduced-motion preferences.

Nine unit-labelled chart groups include shortfall shading and a shared cursor; table tabs expose all 38 comparison, 51 electric, 8 diesel and 9 road channels. CSV preserves all original samples in native no-header order. JSON includes scenario, run identity, output contract and full raw samples, including model sentinels. Chart SVG export includes scenario, model version, units and series labels.

The model comparison flag is preserved exactly: distance >0.0001 km and both cumulative DC/diesel unmet energies <0.000001 kWh. Motor shortfall and mass excess are separate warnings. Individual refill costs use the all-three-positive-prices gate. Cost saving additionally uses the native comparison flag and signed depletion ≥−0.001 kWh. Valid negative savings are shown. The module-specific first-visit guide includes reference values, constrained experiments, playback, interpretation and exports.

This module is an explicit passenger-van exception to the shared Genesis GV70 reference. The supplied study masses, wheel radius and electrical ratings remain unchanged. It does not establish measured vehicle, route, range, tank-pressure, electrochemical, structural or installation validity.

## Reproduce

```sh
.venv/bin/python scripts/bless/compile_model.py
node scripts/sync_assets.mjs
node --test tests/bless/engine.test.mjs
node scripts/bless/export_parity.mjs
.venv/bin/pytest -q
PLAYWRIGHT_BROWSERS_PATH=/private/tmp/atu-playwright .venv/bin/pytest -m e2e tests/e2e/test_bless_ui.py tests/e2e/test_laboratory_flow.py -q
```

The numerical tests check every sample of every native stream at `1e-8 + 1e-9*abs(reference)` (time and flags exact), plus unseen-input invariants, repeatability/independent states, validation, limits, cancellation and sentinel handling. Fresh MATLAB runs were unavailable; unseen combinations have invariant tests, not new native parity claims. The browser evidence is in ignored `test-results/bless/`: desktop/tablet/phone screenshots, default source-energy/power SVGs, full parity CSVs and metadata, overload JSON, and a recorded walkthrough. Chromium is available locally; Firefox and Edge have not been verified in this environment.

## Linked references inspected

Both guides were extracted, including PDF annotations. The linked local thread `01a173ef-809f-7e80-b36a-a3fb541b5c4c` was unavailable; the package is self-contained. All public technical links were accessible. Current documentation is explanatory; supplied R2024b settings and native traces control this port.

- [Simulink Fcn semantics](https://www.mathworks.com/help/simulink/slref/fcn.html)
- [Lookup table semantics](https://www.mathworks.com/help/simulink/slref/1dlookuptable.html)
- [Discrete integration reference](https://www.mathworks.com/help/simulink/slref/discretetimeintegrator.html) — supplied model instead uses explicit UnitDelay recurrences.
- [TypeScript types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)
- [Web Workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers)
- [Reduced motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion)
- [DOE fuel properties](https://afdc.energy.gov/fuels/properties)
- [Mapped CI Engine](https://www.mathworks.com/help/autoblks/ref/mappedciengine.html) — a calibration reference, not a replacement for the supplied diesel equations.
