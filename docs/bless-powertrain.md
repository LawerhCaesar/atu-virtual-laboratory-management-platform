# FCEV Range Extended System — Bless Atisu

Registered under FCEV at `/virtual-lab/fcev/fuel-cell-battery-diesel/`. Approved administrator, lecturer and student accounts use the existing login/access controls. Computation is local to a module Web Worker; no MATLAB service, database migration, payment service or extra runtime dependency is needed.

## Source and conversion

The supplied Python handoff was inspected before execution, then its SHA-256-checked archive was extracted into `docs/reference/bless-battery/`. The original SLX, R2024b graph, both guides, parameter/output catalogs, ten scenario specifications and forty native time histories remain there. They are development references, **not browser assets**. The script's original `validate-results` checker passed all 40 generated streams with its unchanged tolerance and matching model/input metadata. The complete report is `docs/reference/bless-battery/browser-parity-report.json`.

`compile_model.py` checks the three source JSON hashes, resolves local From/Goto tags and hierarchical ports, detects combinational cycles, and generates a dependency-ordered static graph. A build-time expression parser preserves operators (including power), one-based vector indexing, numeric logicals and parentheses. Neither user settings nor imported files are evaluated as code. All 2,063 blocks have path/SID entries in `conversion-map.json`: 697 numerical nodes, scoped wiring and presentation-only elements. All 302 Fcn expressions, 17 UnitDelay states and 106 channels are accounted for. State inputs are committed simultaneously after sampling; t=0 is retained. No generic integrator replaces the delayed recurrences.

The OCV table uses linear point-slope interpolation and clipped extrapolation. Battery initialization retains the trapezoidal OCV inventory integral; the pack kWh scale is applied once, matching the native inventory gain. This floating-point evaluation order matters at zero commanded distance because the native guarded per-distance output magnifies one-ULP differences. No scenario-specific constants, lookup traces, adjusted tolerance or zero-distance special case were added to the engine.

`engine.ts` exposes typed scenario, simulation, sample and result boundaries. `engine.mjs` is its reproducible esbuild output; `graph.mjs` and `catalog.mjs` are the graph compiler outputs. State indices map to the ordered UnitDelay entries in the source parameter catalog and conversion map. Public API: `validateScenario`, `createSimulation`, `stepSimulation`, `runScenario`, `toDisplaySample`, scenario import/export, native result CSV and full result JSON. The simulation owns a copied input snapshot. Unknown versions, malformed arrays and nonfinite values are rejected. Browser limits of 14,400 seconds, 50 kB imported scenarios and numeric magnitude 1e9 are resource/form limits, not validated physical operating ranges. Native operating clamps are reported without replacing the saved raw inputs.

## UI and interpretation

The default view exposes driving, environment, storage and price settings. All remaining component settings and the 18 battery mask entries are editable in Advanced. Ten supplied examples are available; example prices are explicitly illustrative. Inputs can be saved per account/browser or exported/imported. Edits pause playback, cancel an in-flight calculation and mark completed results stale until recalculated. Cancellation terminates the worker; run IDs reject stale messages. Reset clears output. Page hiding pauses playback.

End-of-run cards and charging/cost summaries describe the final route state. The recorded-time slider and plot clicks select a common native sample for chart readings and the four-stream table. Source demands remain explicitly distinguished from delivered-power proof. Fuel-cell chemical/module/DC power, signed battery power, conversion losses and accepted/rejected regeneration are available as analytical channels; no van or physical-flow animation is rendered.

Eighteen unit-labelled charts are stacked within FCEV/battery, diesel and comparison sections. They include SOC with controller thresholds, stored energy, hydrogen, power sharing, battery current/temperature, power/energy shortfalls, conversion losses, diesel consumption and chemical/shaft power, source inventories, commanded distance and refill costs. SVG export includes labelled series and units. The table exposes all 38 comparison, 51 electric, 8 diesel and 9 road channels. CSV preserves all original samples in native no-header order. JSON includes immutable inputs, original contract, complete native samples and the additional study metadata/paired control.

The model comparison flag is preserved exactly: distance >0.0001 km and both cumulative DC/diesel unmet energies <0.000001 kWh. Motor shortfall and mass excess are separate warnings. Individual refill costs use the all-three-positive-prices gate. Cost saving additionally uses the native comparison flag and signed depletion ≥−0.001 kWh. Valid negative savings are shown. The first-visit guide includes distance/reference selection, constraints, recorded-time interpretation, pricing boundaries and exports.

This module uses the supplied Toyota HiAce H300 passenger-van reference. The source study masses, loaded radius and electrical ratings remain separately editable assumptions. It does not establish measured vehicle, route, range, tank-pressure, electrochemical, structural or installation validity.

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

## Analytical distance-study revision (November 2026)

The page is titled **FCEV Range Extended System**, attributed to **Bless Atisu**. The generic van animation has been removed. A full analytical FCEV/battery section appears above the Toyota HiAce diesel section, followed by the common cost/energy comparison. Eighteen charts retain sample-linked cursors and standalone SVG exports; the raw four-stream table and original no-header CSV remain available. End-of-run summary cards are explicitly distinguished from the selected-time chart/table readings.

The FCEV page now uses the supplied 2019 Toyota HiAce H300 Commuter L2H2 specification in its reference panel instead of the common Genesis panel. Those descriptive values do not overwrite source calibration. The source 2650 kg diesel, 3004 kg converted mass, 540 kg common payload, 0.35 m loaded radius and electrical ratings remain editable, with every parameter grouped in basic inputs or accessible advanced tabs.

`study.mjs` wraps the unchanged engine. Distance mode stops at the first original one-second sample meeting the requested commanded distance, or at the entered time cap (maximum 14,400 s). It reports target status, actual commanded distance and overshoot; it does not rescale energy or solve achieved-speed/physical route completion. Duration mode and native examples preserve source duration. A paired battery-only control disables fuel-cell generation on the same converted vehicle, holding mass and requested route fixed. Its complete native samples are exported in study metadata. New tests compare the resulting prefix exactly with a direct native-engine run.

The plug-in planner uses `environment()` from the source engine to compute the chosen SOC energy inventory, then applies grid-to-stored efficiency and constant grid-side input power. This is a charging-energy/time estimate, not a dynamic charging curve or BMS-limited charge simulation. It is an alternative to the native refill-to-initial target, not an additive second grid cost. Native eligibility, surplus-battery restriction and all raw sentinels are preserved. First cumulative DC shortfall, peak motor/DC/diesel shortfalls and gross-mass screening remain separate interpretations. Diesel inventory is an accounting budget with a visible deficit, without adding an empty-tank shutdown.

### Quote provenance and currency

`apps/core/fcev_market.py` provides bounded, cached, fixed-source retrieval through a private role-protected GET endpoint. It permits only explicit HTTPS source hosts, caps response sizes, sets timeouts, caches a refresh for 15 minutes and retains last references on failure. No client-supplied fetch URL is accepted. Initial HTML uses visibly marked stored references so the page can load independently of providers. Automatic-source runs wait for the refresh attempt; custom or native-example runs can proceed. A refresh never silently changes a completed or custom experiment.

- Bank of Ghana daily mid rates: <https://www.bog.gov.gh/treasury-and-the-markets/daily-interbank-fx-rates/>. Direct retrieval during this revision returned 30 October 2026: 11.6200 GHS/USD and 12.9619 GHS/EUR. The effective date is retained separately from retrieval time.
- GOIL Diesel XP: <https://www.goil.com.gh/new-fuel-prices/>. Retrieved quote: GHS18.46/L, effective 17 September 2026. This is a particular published retailer quote, not an assumed national average.
- PURC official reckoner: <https://purcghapp.com/>. The `SLT EV Chg` 100 kWh energy component returned GHS208.63, giving GHS2.0863/kWh. It excludes the separate GHS500 service charge, levies, taxes and public-charger operator margin; the source does not provide a machine-readable effective date. This is a marginal energy reference, not a complete charging invoice.
- International hydrogen benchmark: <https://www.bundeswirtschaftsministerium.de/Redaktion/DE/Artikel/Energie/2021-08-pkw-energiekostenvergleich.html>. Official indexed evidence quotes EUR15.56/kg. Direct source access returned a blocking/challenge page, so this remains explicitly **retained_reference**, with no asserted effective date or fresh-price verification. The operator's current station page also confirms regional/station/pressure variation: <https://h2-mobility.de/unsere-tankstellen/>. The older FAQ's EUR12.85 figure was not substituted as if it were a current universal price.

Hydrogen EUR/kg is converted to USD/kg using BoG EUR/GHS divided by USD/GHS, then into GHS. Engine inputs and native cost channels remain canonical GHS. The USD/GHS selector converts entries and displayed analytical costs; physical samples stay unchanged. Custom rates/prices are labelled and captured with applied study settings. Source dates/status remain visible, and the immutable result records its applied prices, exchange rate and quote book.

### Learning and verification

Every source parameter and unique output channel has a plain-language explanation; info buttons use shared click-again/Escape/outside dismissal. The bottom learning guide includes timing examples, native equations/limits, full HiAce reference, distance and paired-control methods, plug-in planning, cost eligibility and test exercises. A ten-page PDF is generated from the same content and glossary.

Validation covers unchanged native traces, source-preserving distance stopping, paired-route equality, time-cap/noncompletion, charging energy/time, inventory budgets, source parsing and dates, failed-quote retention, access controls, custom-price races, imports/exports, all-editable calibration, cross-module master reset and responsive accessibility. Fresh MATLAB validation of new experiments or measured vehicle validation is not claimed.
