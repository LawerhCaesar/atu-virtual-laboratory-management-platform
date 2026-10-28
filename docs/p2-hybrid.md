# P2 Full-Parallel Hybrid

Integrated into the existing Django platform, under HEV alongside 12 V Micro-Hybrid Stop-Start. No new database schema, MATLAB runtime or frontend dependencies. The server core is the single formula implementation used by both run and comparison APIs. Browser fetches keep calculations off the UI thread.

## Sources and validation boundary

The supplied `LAWRENCE.md` and programmer DOCX are retained under `docs/reference/p2-hybrid/`. Text, tables, relationships and all three embedded architecture/dashboard/power-flow figures were inspected. There are **no external hyperlink relationships** in the DOCX. The optional conversation URL in the Markdown is an unreplaced placeholder. No SLX, model-data/testing guide or thesis was supplied or found alongside the documents. Verification therefore covers the supplied equations and numerical targets, not execution of the original Simulink model or measured Genesis GV70 behaviour.

Model ID: `p2-full-parallel-torque-intensity`; model version `1.0.0`; required formula identifier `simulink-parity-5.1-to-5.20`. The formula identifier records the requested equation contract; it is not an independent Simulink-validation claim. Deterministic run IDs hash the input snapshot, full calibration and version. Case names are labels; identical numerical inputs produce identical IDs.

## Architecture and routes

- `apps/core/simulations/p2_hybrid.py`: framework-independent typed parameter object, metadata, validation, Equations 5.1–5.20, single run and comparison.
- `apps/core/p2_views.py`: active Admin/Lecturer/Student authentication, CSRF enforcement, bounded JSON requests and structured errors.
- `templates/core/p2_hybrid.html`, `static/css/p2-hybrid.css`: responsive platform workbench.
- `static/js/p2-hybrid/{ui,scene,charts}.mjs`: controls, local sessions, exports, recorded-state SVG power flow, charts and comparison. No browser-side duplicate formula core.
- `static/js/walkthrough/steps.mjs`: six tailored tutorial steps, automatic for first visits and reopenable at any time.

UI: `/virtual-lab/hev/p2-full-parallel-hybrid/`

Authenticated services, exact paths without trailing slashes:

| Method | Path | Result |
| --- | --- | --- |
| GET | `/api/v1/hybrid/p2/model-info` | Input/parameter defaults, units, bounds, 23 signal definitions, equations, seven scope groups, limitations |
| POST | `/api/v1/hybrid/p2/simulate` | Metadata, snapshots, summary, warnings/active limits, full time history and scope definitions |
| POST | `/api/v1/hybrid/p2/compare` | Two to four distinct named cases through the same core, aligned summary rows and full histories |

Example authenticated request body (normal Django session cookie and CSRF token required):

```json
{"case_name":"Medium reference","requested_torque_nm":140,"motor_speed_rpm":2500,"initial_soc":0.7,"duration_s":30,"time_step_s":0.01,"parameter_overrides":{}}
```

Comparison body: `{"cases":[{"case_name":"Low","requested_torque_nm":60},{"case_name":"Medium","requested_torque_nm":140},{"case_name":"High","requested_torque_nm":240}]}`.

Invalid bodies/unknown fields/non-finite/out-of-range values return HTTP 400 with `errors` keyed by field. Wrong methods return 405; bodies above 64 KiB return 413. Anonymous access redirects to normal sign-in; inactive/unapproved accounts cannot calculate. Limits: 60,001 samples per run, 120,004 combined comparison samples; duration 0.01–600 s, integration step 0.001–0.1 s. UI and server use the same metadata bounds. Numeric calibration ranges are declared software-domain protections, not manufacturer envelopes.

## Equations and numerical decisions

The core comments retain equation numbering. Torque regimes are Low `<80`, Medium `80≤T<200`, High `≥200` by default, with motor shares 1 and 0.5. Angular speed is rpm×2π/60. Motor torque is limited by 165 Nm and 35,000/(ω+0.001), then disabled strictly **below** SOC 0.30. Engine supplies the residual up to 142 Nm. The clutch opens in Low with acceptable SOC; otherwise it closes. Requested and actual wheel torque use gear 1.00, final drive 3.94 and efficiency 0.90.

Battery demand is motor mechanical power divided by motor/inverter efficiencies 0.92/0.95, plus 500 W auxiliary demand. The supplied quadratic current equation uses Voc 350 V and resistance 0.045 Ω. Its discriminant is protected to [1e−9, 1e12] with an explicit warning if altered. Capacity is 12,000/Voc×3,600 ampere-seconds. Internal loss is I²R. Energy efficiency, RMS current and torque RMSE use the supplied accumulated-integral equations and denominator epsilon 1e−6.

Forward interval integration uses the **left recorded state** consistently for SOC, terminal energy, loss energy and squared metrics. This exactly integrates constant reference cases. Each run includes time zero and the exact final time, including a final partial interval. SOC protection changes on the next recorded state, so a threshold crossing has at most one output-step latency. Reduce the time step to investigate crossings; no hidden event interpolation or new battery control was invented. SOC is clamped to [0,1]. Initial accumulated metrics, including RMS and efficiency, are zero by the supplied equations. Motor share is the pre-limit command, not delivered torque share.

At SOC zero the written equations still allow auxiliary load (and motor torque if the advanced threshold is zero); depletion is flagged. A protected negative discriminant is mathematically defined but physically infeasible. The UI retains warnings and exports them; it does not reinterpret them as successful physical operation.

## Reference results from the implementation

30 s, 2,500 rpm, initial SOC 0.70, step 0.01 s, default parameters; 3,001 samples each.

| Quantity | Low 60 Nm | Medium 140 Nm | High 240 Nm |
| --- | ---: | ---: | ---: |
| Engine torque (Nm) | 0 | 70 | 120 |
| Motor torque (Nm) | 60 | 70 | 120 |
| Requested / actual wheel torque (Nm) | 212.760 | 496.440 | 851.040 |
| Battery power (W) | 18472.498018 | 21467.914355 | 36444.996036 |
| Current (A) | 53.141656 | 61.828395 | 105.561254 |
| Terminal voltage (V) | 347.608625 | 347.217722 | 345.249744 |
| Internal loss (W) | 127.081602 | 172.023767 | 501.443030 |
| Terminal energy (Wh) | 153.937483 | 178.899286 | 303.708300 |
| Loss energy (Wh) | 1.059013 | 1.433531 | 4.178692 |
| Battery energy efficiency (%) | 99.316749 | 99.205063 | 98.642784 |
| Delta SOC (percentage points) | 1.291637 | 1.502773 | 2.565725 |
| Torque RMSE (Nm) | 0 | 0 | 0 |

All supplied tolerances are retained in automated regression tests (0.02 Nm, 2 W, 0.02 A/V, 0.03 Wh, 0.02 efficiency/delta-SOC points). Additional tests cover every equation group, exact regime/threshold boundaries, high-rpm power limiting, engine saturation, low SOC, depletion, discriminant protection, partial final intervals, deterministic results, invalid values, bounded work, authentication, CSRF and API errors.

## Interface and evidence

Presets restore the full reference calibration. Main controls expose torque, rpm and initial SOC with number fields, sliders and minus/plus; Advanced exposes timing and all 19 calibration values. Editing invalidates displayed results and cancels pending UI requests. Run, Reset and Compare operate explicitly. Case names and calibration snapshots accompany every result.

The SVG shows battery → inverter → motor, engine → disconnect clutch → motor/transmission input, then gearbox → final drive → wheels. Paths and component activity follow the selected recorded state; path thickness/pulse rate reflects torque/power. Clutch position, numeric labels and inactive dashed paths supplement colour. Battery fill follows SOC. Inverter displays its conversion efficiency; battery terminal demand includes auxiliary load. Illustrative rotation is not a vehicle speed/distance output. Explicit Play/Pause/Restart and sample scrubbing are available; reduced-motion preference disables animated playback and preserves static inspection. Leaving the page pauses animation.

All seven scope groups are present, with 19 panels separating different units, visible per-series legends, axes, grids, nearest-sample hover/tap readouts, synchronized cursors, shared time-window zoom/reset, and SVG chart export. Peak-preserving chart reduction retains extrema; full samples remain in JSON/CSV. Comparison uses the current calibration, timing, rpm and initial SOC for three torque cases. It provides metric rows, relative changes versus Low (n/a for a zero denominator), nine metric bar charts and overlaid SOC histories.

Save/Load stores one versioned input/calibration snapshot locally, keyed to the active account; it stores no credentials, personal information or assessment submissions. Full JSON includes all inputs, parameters, assumptions, warnings and histories. Compatibility CSV is time plus the exact 12-column `HybridResults` order. Comparison has separate JSON/CSV. Print creates a final-sample summary with input/calibration snapshots and limitations, independent of replay position.

Screenshots generated by browser tests are in ignored `test-results/p2-hybrid/`: `low-1280.png`, `medium-1280.png`, `high-1280.png`, mobile equivalents, charts and comparison. Reproducible complete export examples can be generated into `output/p2-hybrid/` using the pure `simulate()` function; these are local evidence, not runtime dependencies.

## Reproduce and verify

Use the repository’s normal setup (`.venv`, requirements, pnpm install and `pnpm run sync-assets`). Start with `.venv/bin/python manage.py runserver`. Numerical and service tests:

```sh
.venv/bin/pytest tests/test_p2_hybrid.py tests/test_walkthrough.py tests/test_laboratory.py -q
PLAYWRIGHT_BROWSERS_PATH=/private/tmp/atu-playwright .venv/bin/pytest -m e2e tests/e2e/test_p2_hybrid_ui.py tests/e2e/test_laboratory_flow.py tests/e2e/test_micro_hybrid_ui.py -q
.venv/bin/pytest -q
node --check static/js/p2-hybrid/ui.mjs
node --check static/js/p2-hybrid/charts.mjs
node --check static/js/p2-hybrid/scene.mjs
node --test tests/walkthrough/*.test.mjs
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py collectstatic --noinput --settings=config.build_settings
```

Browser tests require installed Chromium (`python -m playwright install chromium`); the local cache path above is this workspace’s existing installation. CI installs its own browser. No TypeScript build is introduced: Python dataclass configuration, Python runtime schema validation and native browser ES modules retain the platform’s established stack. Browser tests capture desktop/mobile visuals, use axe WCAG A/AA checks, and verify numerical displays, low SOC/saturation, editing, comparison, replay, exports, chart zoom, local sessions and print output.

## Boundaries and future adapters

Propulsion-only constant torque and constant motor speed. No P3/P4, regeneration, fuel/BSFC maps, thermal/ageing physics, cell balancing, engine-start transients, vehicle longitudinal motion or drive cycles. GV70 reference dimensions do not change P2 calibration. Future adapters can consume the versioned pure service and its parameter/result schemas; any change to equations or scope requires a new version and regression fixtures. Independent SLX verification remains possible when the original source and testing guide become available.

## Local verification for this release

- Full application suite: **245 passed** (browser tests selected separately).
- Focused P2/reference/API/roles, tutorial and catalogue checks: **43 passed**.
- Browser regression group: **18 passed**, followed by the remaining replay/export test passing after isolating Chromium's cross-document navigation transition from its virtual clock; **19 browser checks passed in total**. P2 desktop/mobile WCAG checks reported no violations.
- Django system checks, migration drift check, Python compilation, native ES-module syntax checks, walkthrough Node checks and static asset collection passed. No migrations or new runtime packages.

GitHub's full PostgreSQL/browser/container/deployment-profile workflow is a separate release check; its outcome must be read from the actual run, not inferred from local checks.
