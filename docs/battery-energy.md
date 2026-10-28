# Battery Energy Management

The BEV catalogue links to `/virtual-lab/bev/battery-energy-management/`. Active administrators, lecturers and students use the existing authentication policy. Existing modules retain their equations and routes.

## Source and validation boundaries

The supplied `CODEX_Battery_Platform_Implementation.md` and complete programmer-guide DOCX are retained in `docs/reference/battery-energy/`. The JavaScript engine is extracted from the marked executable block, with line endings and final newline normalized. A test checks it against the supplied block; UI code never changes its equations. The embedded model identity is `Battery_Energy_Management_Organised.slx`, version 1.0.0, SHA256 `EB530DEEBA66EF27FE20C21EFB7E357D8D61A071467493291E07BCC1AB321931`.

The DOCX paragraphs, tables and relationship links were inspected. Its shared-chat link (`https://chatgpt.com/s/cx_6ade5ed910a081919e5f619b73939bab`) was unavailable; the referenced historical local chat was unavailable through thread retrieval. Neither the original SLX nor `default_simulation.csv` was present in the supplied folder or found by filename in Downloads. The self-contained engine is sufficient to implement the requested module. The guide's historical full MATLAB trace comparison is not represented as a newly executed comparison.

The supplied self-test checks 30 endpoint scenarios, nine default full-channel checkpoints and invariants over 63,398 sample rows. It also checks invalid parameters and inputs, status/reason coverage, view-model mapping, exact CSV columns and power balance. Its actual result is retained in `browser-self-test.json`. Additional controller tests compare the complete 3601-sample default output at 1× and 60× with the supplied engine's synchronous runner; this verifies integration equivalence, not independent physical validation.

## Integration contract

- `battery-platform-kit.mjs`: unchanged source physics, fixtures and reference checks.
- `controller.mjs`: independent per-run state, immutable validated configuration, fixed-step scheduler, timestamped live input edits, event log and raw exports.
- `ui.mjs`: native DOM/SVG controls, eight time-history groups, shared recorded cursor and model-driven energy cutaway.
- `templates/core/battery_energy.html` and `static/css/battery-energy.css`: responsive layout, learning checks and model boundaries.
- `static/js/walkthrough/steps.mjs`: first-visit tutorial plus existing on-demand Module guide.

Each step integrates the previous boundary's input once, applies queued input edits, and observes the next boundary. The default profile switches at 1800 s. The final 3600 s sample is observed without an extra integration step. Live current, mode and ambient changes are queued for the next boundary. Initial conditions, pack parameters, duration and profile change time start a fresh run. Blank values are never coerced to zero. Source validation remains authoritative; the browser limits duration to 14,400 whole seconds for resource control.

The scheduler accumulates wall-clock time at 1×, 10× or 60×, processes at most 120 fixed steps per frame, and retains pending time debt. Pause and hidden-tab handling stop state advancement. Scrubbing reads stored samples, and Resume returns to the most recent calculated state. Page hide cancels the animation callback; page show installs exactly one callback. Reduced motion stops decorative energy travel without changing physics.

The stationary vehicle is an illustrative GV70-style cutaway. The supplied equivalent-pack parameters remain unchanged: 96s24p, 345.6 V nominal, 100.8 Ah, 34.83648 kWh, 200 kg thermal mass. The body is not verified manufacturer geometry. No vehicle motion, driving range, cell-level temperatures or thermal runaway is inferred. SVG fill follows SOC; accepted flow follows actual current; separate dashed intent shows rejection. Temperature color uses the active direction's thresholds. Flow stroke intensity caps at 100 kW for display only.

The CSV contains Time_s plus all 32 native outputs, every recorded second, unrounded. JSON metadata contains source identity, initial parameters and controls, duration, applied input events, pending controls, status/reason events and completion information. Export both files to reproduce an edited run. The interface rounds only display text. Efficiency cards translate the source inactive-direction sentinel into “not active”; raw values remain unchanged.

## Verification commands

```sh
node --test tests/battery-energy/controller.test.mjs
.venv/bin/pytest tests/test_battery_energy.py tests/test_walkthrough.py tests/test_laboratory.py -q
PLAYWRIGHT_BROWSERS_PATH=/private/tmp/atu-playwright .venv/bin/pytest tests/e2e/test_battery_energy_ui.py -m e2e -q
```

Browser checks cover the entire default cycle and export, live edits, pause, reset, new-run calibration, invalid values, hidden-tab pause, lifecycle restart, three viewport sizes, limit presets, reduced motion and axe WCAG checks. Screenshots are written under `test-results/battery-energy/`. These tests validate educational software behavior; they do not establish an automotive control calibration.
