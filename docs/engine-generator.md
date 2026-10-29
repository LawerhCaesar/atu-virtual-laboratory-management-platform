# Engine–Generator Fuel-to-Electric laboratory

The authenticated hybrid catalogue now includes `/virtual-lab/hev/engine-generator/`. The module uses the existing Django route/template, native ES modules and editable SVG rather than a second application or a new HTTP service. Existing simulation equations are unchanged.

## Source audit

Both supplied files are preserved in `docs/reference/engine-generator/`. The DOCX paragraphs, all tables, relationship targets and embedded interface illustration were inspected. The markdown contains a placeholder conversation URL; the DOCX contains `https://chatgpt.com/share/6adce024-70e4-83ea-bbf8-a42e812ab059`, which returned an unavailable/DisabledError response. Neither `EngineGenerator_FuelToElectric_SelfContained.slx` nor its separate model-data guide was found in Downloads. Implementation therefore follows the self-contained equations, map data and baseline summary references in the provided documents. This is not a fresh full-trace Simulink comparison or production-vehicle calibration.

## Architecture and timing

`static/js/engine-generator/engine.mjs` is the single numerical authority. It validates configuration and maps; computes the exact steady, gradual and pulsed profiles; applies SOC support, command rating and enable; interpolates timestamped delayed commands; limits rise/fall rate; interpolates normalized component maps; and calculates shaft torque, fuel mass flow, chemical power, generation, efficiencies, losses, shortfall and residual. All cumulative quantities use trapezoidal integration.

The initial sample is at t=0 with zero ramped command and cumulative totals. Each step advances by dt and applies the external inputs at the new sample boundary. A fractional transport delay interpolates between adjacent timestamped commands, and returns zero before history exists. History retains the necessary interpolation bracket. The last interval is shortened when duration is not divisible by dt; actual timestamps remain in exports. Full and streaming runs use the same step function. The default run has 1201 samples.

External inputs apply to the current step only; omitted fields fall back to the scenario configuration. A caller maintaining a persistent external setpoint should supply that value each step. SOC is an external condition, not integrated battery state. Disabling the set passes through delay and ramp-down; it does not erase stored energy totals. Status uses RAMPING while target tracking is incomplete, DELAYED before nonzero command arrives, LIMITED for active rating restriction, GENERATING for settled generation, and OFF for settled zero output. Invalid configuration throws an actionable error and the UI pauses/disables execution.

Recommended input ranges produce warnings rather than silent clamping. SOC has hard 0–100% bounds. Resource safeguards restrict runs to 100,000 intervals and 86,400 seconds, and maps to 2–1000 points. Extreme finite values that overflow arithmetic fail explicitly. Physically inconsistent imported BSFC/LHV combinations produce a warning; the supplied equations are not silently altered to hide negative losses or efficiency above unity.

## Integration API

```javascript
import {defaults, simulate, initialize, step, EngineGeneratorModule}
  from './static/js/engine-generator/engine.mjs';
const config = defaults();
const complete = simulate(config);
let state = initialize(config);
({state} = step(state, {P_demand_kW: 20, battery_SOC_pct: 40}, 0.1));
const module = new EngineGeneratorModule();
module.initialize(config);
const update = module.step({P_demand_kW: 20, enabled: true}, 0.1);
console.log(update.outputs);
```

The adapter exposes exactly `P_gen_kW`, `eta_f2e_ratio`, `fuel_flow_gps`, `P_shortfall_kW`, and `generator_utilisation_pct`. External fields also include `generator_rating_kW` and `fuel_LHV_MJ_per_kg`. The core has no UI imports or shared mutable simulation state.

## Interface and export contract

The new page offers complete calculation, live pacing, pause/resume, reset, single-step operation, teaching scenarios, numeric/slider/nudge inputs and individual reference resets. Editing begins a fresh run. Hidden-tab handling pauses, page hide cancels animation and page show installs one callback. Live pacing retains accumulated time debt and caps calculation work per frame; it does not enlarge dt.

The stationary vehicle schematic shows fuel, engine, generator and DC link. Power controls flow widths (100 kW visual cap only); calculated labels show the actual powers. External SOC is labelled as fixed. No vehicle speed, range, wheel torque, emissions or battery electrochemistry is fabricated. Reduced motion stops decorative particle travel without changing calculations.

Five scientific chart groups have labelled units, shared recorded time, a cursor, hover time, 10/30 s inspection windows, series toggles and individual SVG downloads. Channels of different units use separate axes. Charts decimate only drawing points; JSON/CSV retain every sample. Component maps are editable as validated JSON, with a numeric table and source/description/version fields. Scenario JSON includes inputs, settings, maps, model version and timestamp. Full JSON adds samples, summary and warnings. CSV starts with a `# metadata` record containing configuration and provenance, followed by the channel header and sample rows; skip that first metadata record when using a conventional table reader. Chart SVG embeds the same configuration metadata plus displayed series and window. The integration payload is copyable, and a print stylesheet produces a concise numerical summary.

## Baseline validation

| Quantity | Implementation | Supplied reference |
|---|---:|---:|
| Generated energy (kWh) | 0.5896190751 | 0.5896 |
| Fuel energy (kWh) | 1.8824256750 | 1.8824 |
| Loss energy (kWh) | 1.2928065999 | 1.2928 |
| Shortfall energy (kWh) | 0.0153785949 | 0.01538 |
| Fuel (g) | 157.5984286067 | 157.60 |
| Case efficiency (%) | 31.3223030770 | 31.32 |
| Mean utilization (%) | 58.9619075130 | 58.96 |
| Peak generation (kW) | 22.5 | 22.50 |
| Maximum absolute residual (kW) | 3.553e-15 | below 1e-9 |

## Run and test

```sh
.venv/bin/python manage.py runserver 127.0.0.1:8765
node --test tests/engine-generator/engine.test.mjs
.venv/bin/pytest -q
PLAYWRIGHT_BROWSERS_PATH=/private/tmp/atu-playwright .venv/bin/pytest tests/e2e/test_engine_generator_ui.py -m e2e -q
```

Use the project's configured database and an approved local account; no new credentials are embedded. Tests cover baseline references, fractional delay, full/stream equivalence, disable response, map replacement, SOC/rating/profile behavior, invalid data, exports, live pause, responsive layouts and WCAG checks. Visual evidence is stored under `test-results/engine-generator/`: baseline desktop/mobile, limited-output scenarios, flow-desktop, and engine-generator-preview.webm. These are working interface captures, not mock-ups.

The prior release's GitHub failure was also inspected: BrakeLab's BEV catalogue assertion still expected one model, and the engine 3D test allowed wall-clock time to advance between browser actions, triggering intentional stall protection on slow CI. The catalogue expectation and controlled-clock test setup were corrected without changing those modules' scientific behavior.
