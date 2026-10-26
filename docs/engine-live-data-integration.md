# Engine Live Data Demonstration integration

Specification: the supplied `Engine_Live_Data_Codex_Virtual_Platform_Package`,
revision 2026-10-12. Implementation date: 15 October 2026.

## Integration map

The host is Django 5.2 with server-rendered templates, vendored Bootstrap 5.3,
plain JavaScript assets and pytest/Playwright/axe verification. There is no
existing chart library or client-side application framework. The engine feature
therefore uses local ES modules and accessible SVG plots without adding a
dependency, frontend framework, API or deployment.

- Route: `/virtual-lab/engine-live-data/`, named `core:engine_live_data`.
- Navigation: **Virtual laboratory** and each role's **Choose a system** card
  open `/virtual-lab/`. Select ICE, BEV, FCEV, Hybrid or Vehicle Dynamics, then
  enter its branded catalogue at `/virtual-lab/systems/<slug>/`. Only ICE has
  implemented models; other catalogues contain just an empty-state message,
  with no speculative/future model listings or launch links.
  **Engine Live Data Demonstration** remains one model. Its four learning
  sections remain inside the simulation, alongside Overview. ICE also lists
  the separate [Fuel Delivery Optimisation model](fuel-delivery-integration.md);
  that addition does not alter this model's equations, controls or 3D assets.
  Legacy deep links still accept allowlisted `?view=` values (`fuel`, `idle`,
  `cooling`, `startRun`); these do not create separate model entries.
  Selection affects presentation only; the solver and 3D scene remain shared,
  OFF and paused until Run. Invalid view values fall back to Overview.
  Existing direct engine bookmarks still work; navigation always starts with
  system selection and simulation breadcrumbs return to the ICE catalogue.
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
- Input editing: large sliders, 44-pixel minus/plus controls, direct numeric
  entry and individual numeric-default buttons share the same controller.
  RPM nudge buttons use 50 rpm; voltage uses 0.01 V; other nudges use 1 unit.
  Numeric editing recalculates immediately without advancing virtual time.
  Presets/start/stop controls precede the sensor list. A local search hides
  nonmatching inputs without changing their values or the emergency-stop latch.
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

## Optional 3D cutaway (17 October 2026)

The simulation page automatically embeds the WebGL 2 view near the top,
above the sensor forms. It starts paused/OFF, never automatically starting an
engine sequence. The shared Run/Pause/Reset/CSV toolbar remains directly above
the viewer's advanced options, directly below its canvas, with a jump link to sensor/start controls for mobile use. The canvas
precedes advanced view options, and full safety/physical-stage limitations
remain available in an expandable section. **Close 3D view** releases the GPU;
**Load 3D engine** retries after closing or a graphics failure. The view
uses a locally bundled Three.js renderer, no CDN, external model or new backend.
`frontend/engine-cutaway.mjs` is the editable renderer source;
`static/js/engine-live-data/kinematics.mjs` contains testable presentation-only
geometry. `node scripts/sync_assets.mjs` reproducibly builds the checked-in
`cutaway.bundle.mjs` and copies the Three.js licence. Render serves that bundle
without requiring Node at runtime. Dependencies are pinned in the lockfile;
package install scripts are disabled. CI checks bundle reproducibility.

Motion advances only on completed 0.05-second simulation steps, using the
student-selected RPM during CRANK/RUN. Run/Pause, Reset and emergency stop share
the existing model controls. Slow-motion scaling affects only visual crank
phase, never solver time, input values, recorded history or CSV. Smooth drawing
interpolates the visual angle between updates; it is not an extra solver.
Turning off animation freezes the illustrative phase. Reduced-motion users
start with motion disabled. Graphics failure/context loss leaves the existing
calculations and graphs available. Closing the view releases GPU resources.

This is a **generic educational mechanism, not an accurate 1NZ digital twin**:
arbitrary scene geometry (crank radius 0.36, rod length 1.25), assumed firing
order 1–3–4–2 and idealised stroke-boundary valves without overlap or VVT.
Piston motion uses the slider-crank equation and preserves rod length. Cylinder
zero is firing TDC; power/exhaust/intake/compression each occupy 180 crank
degrees. Spark indicators apply the calculated advance to that assumed cycle.
Injection indicators show enable and pulse-width magnitude; no measured
injection phase, flow or spray is implied. The coolant marker is a temperature
indicator, not a thermal field. Fan/virtual-pump readouts are duty commands,
not measured RPM or fluid flow. No torque, combustion pressure, power, fuel
consumption or physical validation is claimed. High-speed screen aliasing is
explicitly disclosed; default playback is 0.02×.

Tests cover dead centres, connecting-rod length, stroke/firing-order mapping,
spark gating/advance, motion gating/scaling, unchanged model/CSV, desktop/mobile
WebGL interaction, pause/reset/emergency stop, reduced motion, keyboard camera
controls, local asset failure, context loss and accessible text alternatives.

### Animation and transition refinement

The cutaway now includes smooth sinusoidal-squared valve lift, half-speed
illustrative overhead camshafts, a rotating flywheel, translucent stroke-colour
volumes and optional directional intake/exhaust markers. These teach cycle
sequence and mechanism motion; the gas volumes are **not** combustion, pressure,
fuel-spray or heat-transfer results. Flow markers and fan rotation use arbitrary
teaching cadence (600 rpm at 100% duty before playback scaling), not an actuator
speed/flow prediction. Fan and virtual-pump motion observe calculated duty
commands, completed virtual steps, Pause, Reset and emergency-stop gating.

The scene linearly interpolates toward each completed batch's visual phase over
200 ms rather than changing the solver cadence. It introduces a visual-only
lag of up to one batch; exact numeric readouts and recorded CSV remain unchanged.
At visual crank rates above 300 rpm (2.5 four-stroke cycles/s per cylinder),
stroke colours become steady neutral, flow markers are suppressed and the
enabled spark indicator stays steady to avoid rapid flashing. There is no
flame strobe. **Illustrative flow effects** can be disabled separately.
Reduced-motion defaults disable both animation and effects; changing the system
preference to reduced motion while the view is open also stops them.

`static/css/motion.css` provides modest entrance, card/button hover/focus and
native cross-document view transitions where supported. It does not intercept
links, submissions, approvals or logout. Engine system-view changes use a short
transform-only reveal. No text/background colour interpolation, continuously
looping decorative animation, new library or hidden-until-JavaScript content
is introduced. Reduced-motion preferences disable these transitions.

## Reference UI alignment (17 October 2026)

The existing Django interface now follows the supplied reference site's navy,
gold, serif headings, pale workspace surfaces, rounded cards and two-column
welcome/access composition. The university crest was sourced from the same
official asset displayed by the reference:
https://atu.edu.gh/wp-content/uploads/2024/07/ATU-LOGO-AUTHENTIC-edit-1024x980.png
and is served locally as `static/atu-crest.png`, without third-party page requests.
The cohort photo remains an explicitly labelled placeholder.

Role cards lead to the existing secure login; they do not grant a selected role,
add prototype/sample credentials or bypass approval. Forms, CSRF protection,
role checks, assessments, evidence access, calculations and database schema are
unchanged. The reference Site itself was not modified.

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
