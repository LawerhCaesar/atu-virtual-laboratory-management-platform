# Handover Revision — 2026-10-12

## Purpose

The colleague already has a virtual automotive platform in development. This revision makes `CODEX_MASTER_PROMPT.md` authoritative: **do not build a new platform; implement only the Engine Live-Data Demonstration section inside the existing repository.** The `.txt` prompt is identical.

Codex must inspect the existing architecture and reuse its routing, navigation, components, styles, state conventions and development workflow. The handover requires only the engine section and the minimal host wiring needed to expose it. It excludes unrelated redesign. If the actual repository is unavailable, Codex must request its location/access instead of creating another application.

The physical 1NZ setup is separate and has no electric water pump. Virtual ECT1/ECT2, the duty-controlled fan and the virtual electric water pump remain part of the virtual cooling model. The virtual and physical stages are tested independently with no comparison.

## Files revised

- `CODEX_MASTER_PROMPT.md` and `CODEX_MASTER_PROMPT.txt`: explicit scope, authority, repository-inspection workflow, preservation requirements and integration acceptance criteria.
- `START_HERE.md`: colleague-facing overview, replacement instructions, package guide and reference-test command.
- `UI_AND_BEHAVIOUR_SPEC.md`: engine-section identity, host-platform layout boundary and virtual/physical clarification.
- `ACCEPTANCE_TESTS.md`: independent-stage boundary and additional host-integration checks; all original acceptance requirements and numerical cases retained.
- `engine_live_data_spec.json`: section title and additive scope/integration metadata. Existing engineering fields and canonical signal identifiers retained.
- `prototype/README.md`: clear reference-only role and explanation of the retained prototype title/layout.
- `REVISION_NOTES.md`: this revision and verification record.

## Engineering and reference preservation

All 14 original files remain at their original relative paths. The seven original files outside the documentation/specification updates are byte-for-byte identical:

- `reference/engineLiveDataModel.mjs`
- `reference/engineLiveDataModel.test.mjs`
- `prototype/index.html`
- `prototype/app.js`
- `prototype/styles.css`
- `source/SIGNAL_MAP.csv`
- `source/MODEL_ASSUMPTIONS.txt`

The JSON simulation settings, inputs and caps, formulas, state machine, outputs, presets, dependency flows and chart requirements are unchanged. Existing scope flags remain unchanged; additional flags state the integration boundary and independent testing explicitly. `applicationName` and `ui.pageTitle` now read `Engine Live-Data Demonstration` while keeping the original JSON keys.

Master-prompt sections 5–7 (canonical inputs, exact calculation logic and output categories) are unchanged. All fenced equations, state diagrams and preset blocks are unchanged. Original acceptance cases 1–15 and their expected values are unchanged; section 16 adds integration checks.

The standalone prototype retains its original “Engine Live-Data Virtual Laboratory” title and executable files. The updated README and authoritative master prompt explain that this is a reference demo. Historical source notes about future calibration do not authorise a model change during this integration.

## Verification

- The preserved Node.js reference suite was executed successfully: **11 tests passed, 0 failed**. Its calculation module and test file remain byte-for-byte unchanged after the handover revision.
- A preservation check confirmed all 14 original files remain, the seven code/source assets are unchanged, the engineering JSON values are unchanged, master-prompt engineering sections and fenced blocks are unchanged, and the original acceptance cases remain intact.
- The Markdown and text master-prompt files are byte-for-byte identical.
- The revised ZIP was reopened and its file contents checked against the revised package files.

To rerun the existing reference suite from this package directory:

```sh
node --test reference/engineLiveDataModel.test.mjs
```

The 11 automated reference tests do not cover every manual/UI acceptance item. This revision prepares the handover; it does not claim that the colleague's platform has been implemented, built or tested. The colleague's Codex implementation must complete the host integration checks. No physical-stage tests or virtual-versus-physical comparison were performed.

## Replacement filename

Use `Engine_Live_Data_Codex_Virtual_Platform_Package.zip` to replace the earlier handover ZIP. The top-level folder keeps the same name. Replace only the handover files, not the colleague's platform source or unrelated work. The original archive name is retained for convenience; the implementation scope is one engine section inside the existing platform.
