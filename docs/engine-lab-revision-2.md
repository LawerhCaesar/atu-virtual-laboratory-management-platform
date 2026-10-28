# Engine Live Data Demonstration — revision 2

The restored ICE model is at `/virtual-lab/engine-live-data/`, alongside Fuel Delivery Optimisation. It uses the existing Django shell, active-role access, shared tutorial and browser-run JavaScript; no MATLAB, server calculation API, hardware connector or new dependencies are required.

## Source and verification boundary

The user-supplied [master prompt](reference/engine-lab/master-prompt.md) is the authoritative executable contract; the [programmer guide](reference/engine-lab/programmer-guide.docx) explains its interface and acceptance cases. Both are retained in the repository. The guide's embedded picture and external hyperlink relationship were inspected. The optional shared conversation URL could not be fetched in this environment, and the referenced Codex thread could not be accessed; both are optional, and the provided prompt contains the complete model.

`static/js/engine-live-data/reference.mjs` is the supplied TypeScript reference transpiled to dependency-free ES2022 with the project's existing esbuild. It preserves the exact fixed-step equations, branch priority, threshold inequalities and double-precision accumulated state elapsed. The initial state is OFF with sample index −1. The first recorded call produces sample 0 at time 0; thereafter time is sample index × 0.05 s. No physical rig comparison or OEM calibration is claimed.

The retained `model.mjs` contains legacy functions and the relationship-description helper; `controller.mjs` uses the revision-2 `reference.mjs` as its calculation core. `ui.mjs`, `schematic.mjs` and the optional existing 3D cutaway consume the controller's same sampled snapshot. Full-precision values are retained; UI formatting is presentation only.

## Behaviour

- Eight numeric sensor inputs have number, slider and −/+ controls. Finite values are capped with an accepted-value message; invalid or blank input retains the last accepted number. ECT controls show an input-temperature preview, and the sampled output panels show the calculated temperatures.
- Three operating switches are simulated. While running, Start and Stop create ten-sample pulses; Stop clears a pending Start. Emergency is latched until Clear emergency or Reset all. Start/Stop are disabled while paused.
- Run/Resume accumulates wall-clock time into fixed 0.05-second steps. A long stall or hidden tab pauses without catching up. Step advances once while paused. Changes to controls remain pending until a sample; readouts and history show the previous sample until then. Reset pauses, clears history and returns to the unrecorded preview. Presets reset the experiment but preserve a latched emergency.
- Event history records state changes and blocked-start reasons. The schematic shows virtual ECTs, battery, simulated authorisation, starter, fuel pump, injector, ignition, fan and a virtual electric pump. Its labels and optional 3D visual consume the same sampled outputs. Illustrative animation pauses with the simulation and respects reduced motion.
- Overview and four detail panels expose all 30 numeric outputs and the state label. Each system's unit-separated graphs have legends, a common sampled time axis, selected-sample readout and keyboard-operable history slider; state/binary plots are stepped. A selector can add other signals. The retained rolling window has at most 1,201 samples; CSV exports precisely those historical accepted inputs and outputs and is disabled before the first sample.
- The first-visit tutorial describes starting, testing, pausing, stepping and exporting; it can be reopened from Module guide. The physical 1NZ setup is separate, has no electric water pump and is not compared to this virtual stage.

## Reproduction and validation

Run locally with `.venv/bin/python manage.py runserver`; open the ICE catalogue after signing in. Checks:

```sh
node --test tests/engine/*.test.mjs
.venv/bin/pytest -q
PLAYWRIGHT_BROWSERS_PATH=/private/tmp/atu-playwright .venv/bin/pytest -m e2e tests/e2e/test_engine_demo.py tests/e2e/test_engine_cutaway.py tests/e2e/test_laboratory_flow.py tests/e2e/test_fuel_delivery_ui.py -q
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py collectstatic --noinput --settings=config.build_settings
```

Regression tests include ECT breakpoints, every input cap, invalid types, warm/lean/rich/cold/hot/idle reference values, slow-crank timeout and priority, strict >15 °C disagreement, emergency override, low battery, sample timing, paused edits, pulse duration and historical CSV. Browser checks cover active login, engine interactions, 3D/reduced-motion/fallback, chart controls, accessibility and responsive widths, plus ICE catalogue and existing fuel flows. Captured evidence is in ignored `test-results/engine-live-data/`.

The equations are educational virtual control relationships. Sensor inputs are imposed; outputs do not create engine acceleration, coolant transport, fuel consumption, combustion pressure or road motion. Animation is qualitative and does not validate the model against physical hardware.
