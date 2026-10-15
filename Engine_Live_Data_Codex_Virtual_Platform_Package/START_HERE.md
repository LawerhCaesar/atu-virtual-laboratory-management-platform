# Engine Live-Data Demonstration — Existing-Platform Integration Handover

**DO NOT BUILD A NEW PLATFORM. Add only the Engine Live-Data Demonstration section inside the colleague's already-existing virtual automotive platform/repository.**

Revision: 2026-10-12. The ZIP and its top-level folder keep the original name `Engine_Live_Data_Codex_Virtual_Platform_Package` so this handover can replace the earlier package. That filename does not define the implementation scope.

## Project title

**Virtual Modelling and Physical Demonstration of Engine Live-Data Relationships for Virtual-Platform Integration**

## What this package is for

The colleague has already started the automotive platform. This package supplies the engineering specification for **one Engine Live-Data Demonstration section** inside it. It gives Codex the model details needed to implement that section using the platform's existing architecture.

`CODEX_MASTER_PROMPT.md` is authoritative for scope and integration. Its `.txt` copy is identical. Codex must inspect the existing repository first, reuse its routing, components, styles and state conventions, and avoid redesigning unrelated platform areas. If the repository is unavailable, Codex must request its location/access instead of creating a substitute platform.

The virtual laboratory teaches students how one engine live-data parameter affects another:

**controlled student input → capped sensor/operating value → ECU calculation → commanded output → displayed live-data result**

The Simulink model is the engineering reference behind these supplied specification and reference files. The integrated engine section must reproduce the supplied logic without requiring MATLAB on the learner's computer.

## Four models within the engine section

This single section contains four learning systems:

1. **Fuel trim and injection control** — oxygen-sensor voltage, lambda estimate, STFT/equivalent closed-loop correction and injector pulse width.
2. **Idle and ignition control** — target idle speed, actual RPM, RPM error, idle-control duty and ignition timing.
3. **Cooling control** — virtual ECT1 and ECT2 voltages and temperatures, sensor agreement, duty-controlled fan and a **virtual electric water pump**.
4. **Start/run and fuel-pump control** — ignition, fingerprint authorisation, voice/manual start request, fuel-pump prime, cranking, injection/ignition enable, running and shutdown.

## Important boundary

The **physical stage is separate**. It uses a Toyota 1NZ engine, a third-party programmable ECU and the planned peripherals. The physical 1NZ setup has **no electric water pump**. The virtual and physical stages are **tested independently, with no comparison**: no comparison page, combined result dataset, agreement/error metric or numerical-agreement claim. The virtual cooling model does not specify matching physical hardware.

## Recommended use

1. Replace the earlier handover ZIP/folder with this revised package. Keep the handover distinct from the colleague's platform source files.
2. Open Codex in the colleague's actual existing platform repository and give it `CODEX_MASTER_PROMPT.md` (or the identical `.txt` copy).
3. Keep the complete extracted package accessible alongside that repository so Codex can read the exact signal definitions, equations, UI requirements, prototype and test cases. The handover folder itself is not the platform repository.
4. Codex should inspect the platform, identify the section's integration points, and implement all four models as views inside the engine section using existing routing, components, styles, state management, authentication and chart conventions.
5. Use `prototype/index.html` only as a visual and functional reference. It opens in a normal browser without installation. Its standalone layout is not a platform template or a required redesign.
6. Run the preserved reference tests with `node --test reference/engineLiveDataModel.test.mjs` from this package folder. During integration, adapt them to the host's test runner and complete the model and integration checks in `ACCEPTANCE_TESTS.md`.

## Package contents

- `CODEX_MASTER_PROMPT.md` — the complete ready-to-paste Codex instruction.
- `CODEX_MASTER_PROMPT.txt` — identical plain-text copy of the authoritative prompt.
- `engine_live_data_spec.json` — machine-readable inputs, outputs, ranges, equations, state logic and UI structure.
- `UI_AND_BEHAVIOUR_SPEC.md` — detailed description of what should appear in the application.
- `ACCEPTANCE_TESTS.md` — expected outputs for verification.
- `reference/engineLiveDataModel.mjs` — dependency-free reference calculation engine.
- `reference/engineLiveDataModel.test.mjs` — executable Node.js tests.
- `prototype/index.html` — standalone browser prototype.
- `prototype/app.js` and `prototype/styles.css` — prototype logic and styling.
- `source/SIGNAL_MAP.csv` and `source/MODEL_ASSUMPTIONS.txt` — copied from the working R2024b Simulink builder package.
- `REVISION_NOTES.md` — scope changes, preservation details and verification results for this revised handover.

## Accuracy statement

The equations are deliberately simplified educational relationships. They are not Toyota 1NZ, OEM or production ECU calibration data and must not be used to control a road vehicle or safety-critical hardware.
