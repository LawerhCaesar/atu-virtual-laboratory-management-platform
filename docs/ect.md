# Amachie engine coolant temperature laboratory

Route: `/virtual-lab/ice/coolant-temperature/` (active student, lecturer or administrator account required).

## Source and integration

The uploaded Markdown and Word guide are retained in `docs/reference/ect/`. The single executable block was extracted with LF line endings into `static/js/ect/Amachie_ECT_Virtual_Platform.js`. SHA-256 remains `72daeb446e8eac9b14ba408e7bcbe6fb4bc473489942547a55e294db9c9e42cc`; its numerical engine and reference interface are unchanged. `platform.js` mounts it, applies platform typography and tutorial highlights, and moves the existing calibration form above the visualisation. The shared tutorial can resolve explicit `host >>> shadow-selector` targets without changing the reference runtime.

The core is independent of rendering: `validateConfig`, `createEngine`, `simulate`, `toCSV` and `verifyReferenceCSV` work in Node CommonJS. The browser computes full traces at fixed numerical steps and only replays samples; it does not send simulation data to a backend. The server enforces page access using the platform's existing roles. There are no new dependencies, migrations or external runtime requests.

All nine original output names and three auxiliary signals are retained. The first-order sensor, NTC Beta equation, divider, ADC rounding/clamping and guarded inverse remain unchanged. Default RK4 step is 0.01 s, duration 120 s, yielding 12,001 samples. At the 20 s step boundary Ts is 20.0444444444 C. At 120 s Ts is 100 C, R approximately 174.379943 ohm, V 0.327243011 V, ADC 268 and ECU estimate 100.001692613 C.

The five plot groups, schematic and readings share a sample cursor. Playback speed changes presentation only; hidden pages pause. Settings apply atomically and reset after validation; invalid edits preserve the last valid run. CSV contains the entire computed trace, not merely the played portion, and retains both validity flags. Input clamping and ADC rail invalidity are separate conditions. A rail temperature is a finite fallback and must remain labelled invalid.

The common Genesis GV70 reference is context only. Vehicle geometry, fan behaviour, coolant flow, combustion and fuel use do not enter these equations. The schematic is stationary and its moving dashes illustrate signal activity only.

## Document and link audit

Both full document text and DOCX relationship hyperlinks were inspected. The DOCX contains an older snapshot in addition to the visible current snapshot:

- https://chatgpt.com/s/cx_6ade6c06f2308191a15a14ab6b0dfa08 — inaccessible through the web reader (DisabledError).
- https://chatgpt.com/s/cx_6ade5ed910a081919e5f619b73939bab — inaccessible through the web reader (DisabledError).
- https://www.mathworks.com/help/simulink/ug/fixed-step-solvers-in-simulink.html — accessible; fixed-step solver reference.
- https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame — accessible; playback timing reference.
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion — accessible; reduced-motion reference.

The referenced native model `David_Amachie_ECT_Complete_Interactive_Model.slx` and `ECT_Validation_2026-10-25/default_run.csv` were not found in the supplied Downloads tree. The Windows source path is provenance, not a downloadable link. The handoff reports a full native comparison, but that comparison has not been independently repeated in this integration. Do not substitute the JavaScript export for the native reference. Other presets have analytical/guard coverage rather than native-trace parity.

## Repeatable checks

```sh
node static/js/ect/Amachie_ECT_Virtual_Platform.js --self-test
.venv/bin/pytest tests/test_ect.py tests/test_laboratory.py tests/test_walkthrough.py -q
PLAYWRIGHT_BROWSERS_PATH=/private/tmp/atu-playwright .venv/bin/pytest tests/e2e/test_ect_ui.py -m e2e -q
# When the original independent CSV becomes available:
node static/js/ect/Amachie_ECT_Virtual_Platform.js --verify-csv /path/to/ECT_Validation_2026-10-25/default_run.csv
```

The source self-test has 37 checks. Platform browser tests cover heating, cooling, fixed 85 C, clamping, both rails, atomic invalid and valid settings, full-resolution CSV, playback/pause, hidden-page pause, reset, keyboard scrubbing, tutorial shadow targets, reduced motion, mobile overflow and axe WCAG checks. Desktop/mobile screenshots are generated under `test-results/ect/` for initial, warm-up, final and rail-invalid states.
