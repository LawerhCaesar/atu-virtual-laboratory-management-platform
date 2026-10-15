# Engine Live-Data Demonstration integration

Specification: the supplied `Engine_Live_Data_Codex_Virtual_Platform_Package`,
revision 2026-10-12. Implementation date: 15 October 2026.

## Integration map

The host is Django 5.2 with server-rendered templates, vendored Bootstrap 5.3,
plain JavaScript assets and pytest/Playwright/axe verification. There is no
existing chart library or client-side application framework. The engine feature
therefore uses local ES modules and accessible SVG plots without adding a
dependency, frontend framework, API or deployment.

- Route: `/virtual-lab/engine-live-data/`, named `core:engine_live_data`.
- Navigation: **Engine live data** in the existing authenticated navigation.
- Access: existing active Administrator, Lecturer and Student roles, with the
  existing first-login password-change and suspension controls intact.
- Layout: `templates/base.html`, existing Bootstrap controls, panels, colours,
  typography, messages, dashboard link and responsive navigation.
- Pure model: `static/js/engine-live-data/model.mjs`, copied byte-for-byte from
  the supplied executable reference. It has no DOM, chart or API dependencies.
- Metadata: `spec.mjs` preserves the supplied JSON as a local module.
- State: `controller.mjs` owns raw/capped inputs, internal state, running status,
  momentary requests and history. Calculations advance in 0.05-second steps;
  the browser batches four calculations per 200 ms render.
- Lifecycle: page navigation clears the interval. Pausing preserves virtual
  time, state and recorded history. Reset restores all defaults, OFF, paused
  status and empty history. Emergency stop also works while paused and stays
  latched until reset. Presets cannot bypass the state machine or release it.
- Charts: each signal has its own labelled scale and units, a common virtual
  time axis, a descriptive title and a current-value tooltip. This avoids
  overlaying RPM, temperatures, voltages and percentage signals on one scale.
- Export: browser-generated CSV contains canonical accepted inputs, outputs,
  statuses, simulation time and state elapsed time. It includes the current
  displayed state and no physical-stage data or automatic assessment result.

The static modules load with the authenticated page; calculations then run
without MATLAB, hardware access or network calculation requests.

## Requirement coverage and evidence

| Package acceptance cases | Implementation and checks |
| --- | --- |
| 1: input capping | All canonical min/max/default definitions checked against JSON; browser cap notice verified. |
| 2: ECT checkpoints | All nine supplied voltage/temperature checkpoints retained in model tests. |
| 3–5: stoichiometric, lean and rich fuel | Original exact numerical tests; warm and lean pulse widths also checked in the integrated browser. |
| 6: closed-loop disabling | Both coolant and RPM threshold cases checked. |
| 7: idle/ignition | Original RPM error, duty and ignition timing test retained. |
| 8–10: normal, high-demand and disagreement cooling | Original cases plus high-demand test; normal and disagreement outputs checked in the browser. |
| 11–13: battery blocking, normal start and crank timeout | Original low-battery/start tests; controller timeout, shutdown and branch-priority checks. |
| 14: emergency stop | Original RUN shutdown test, paused/latching controller checks, browser command-zeroing/export checks. |
| 15: UI integration | Browser run/pause/reset, live graphs, CSV, immutable output controls, disclaimer and dashboard return; desktop/mobile axe and overflow checks. |
| 16: host integration | Existing shell/navigation/authentication reused; no model recalibration, separate app, unrelated redesign or physical comparison feature. |

The reference uses floating-point elapsed-time accumulation. Transition checks
retain that implementation, including a possible one-step floating-point
boundary at 5.0/0.5 seconds. No engineering formula, threshold or branch priority
has been changed to hide this.

## Local usage and verification

Observed local results for this increment:

- Ordinary suite: **158 passed**, with 59 browser cases excluded.
- Model/controller contract suite: **20 passed**, including the eleven original
  reference cases. The copied model matches the supplied reference byte-for-byte.
- Existing browser workflows/accessibility cases: **56 passed** in the full run.
- Final engine browser workflow and desktop/mobile checks: **3 passed** after
  fixing feature control contrast and SVG accessibility markup.
- Ten engine axe reports: zero detected violations; nine incomplete findings
  remain for manual review. This is not full accessibility certification.
- Django checks and static collection pass; no migration changes are required.

The full browser run initially found two engine contrast failures; the final
focused rerun above passed after the correction. Remote CI is the gate for a
single complete run on PostgreSQL with the final commit.

Start the existing Django application as described in the main README, sign
in with an active account, complete any required password change and choose
**Engine live data**. Load a preset, enable ignition and authorisation, press
the voice/manual start button and press Run. Presets do not start the engine.

```bash
pnpm run test:engine
.venv/bin/pytest -q
.venv/bin/pytest -m e2e tests/e2e -q
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
pnpm run sync-assets
```

The browser suite uses an isolated temporary database and synthetic fixtures.
If bundled Chromium is absent, the existing supported local alternative is
`ATU_BROWSER_CHANNEL=chrome .venv/bin/pytest -m e2e tests/e2e -q`.
The ordinary pytest suite also invokes the Node engine contract tests.

The preserved handover's reference suite can be run independently:

```bash
node --test Engine_Live_Data_Codex_Virtual_Platform_Package/reference/engineLiveDataModel.test.mjs
```

Engine screenshots and ten desktop/mobile accessibility reports are generated
under `test-results/engine-live-data/`. Generated QA files are ignored by Git.
Automated accessibility checks and numerical verification do not constitute
a participant study, human usability review or physical-engine validation.

## Files delivered

Created:

- `static/js/engine-live-data/model.mjs` — preserved pure engineering model.
- `static/js/engine-live-data/spec.mjs` — canonical metadata and presets.
- `static/js/engine-live-data/controller.mjs` — simulation state and CSV export.
- `static/js/engine-live-data/ui.mjs` — controls, explanations, views and plots.
- `static/css/engine-live-data.css` — feature-scoped layout and styles.
- `templates/core/engine_live_data.html` — content within the existing shell.
- `tests/engine/model.test.mjs` — adapted original eleven reference tests.
- `tests/engine/controller.test.mjs` — remaining engineering/controller cases.
- `tests/test_engine_routes.py` — host access checks and Node-test bridge.
- `tests/e2e/test_engine_demo.py` — integrated workflows and accessibility checks.
- `docs/engine-live-data-integration.md` — this integration/evidence guide.

Changed:

- `apps/core/views.py`, `apps/core/urls.py` — feature route and role checks.
- `templates/base.html` — authenticated engine navigation link.
- `package.json` — Node model/controller test command.
- `README.md` — feature entry and integration guide.
- `.dockerignore` — omit the preserved handover package from runtime images.

The supplied handover folder is retained unchanged as engineering source
material, separate from runtime source. No database migration or new service
is needed for this feature. The separate physical 1NZ stage has no electric
water pump, and its evidence is not compared or combined with these virtual
results.
