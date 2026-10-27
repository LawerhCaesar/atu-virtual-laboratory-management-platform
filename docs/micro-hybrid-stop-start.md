# 12 V micro-hybrid stop-start implementation

The provided master task is the available source of equations and acceptance values. The referenced Simulink model, data guide and Chapters 1–3 were not present in the uploaded directory; parity with those files has not been independently verified.

Implementation plan: use the existing Django authenticated laboratory route and browser-side ES modules; implement the reference equations as a pure function with explicit validation and warnings; register one HEV model and a tailored walkthrough; build responsive inputs, decision, results and an illustrative 2D operating sequence; provide local export and comparison; test the reference and inhibit cases, browser interactions, accessibility and responsive layouts before deployment.

The shared project conversation referenced in the programmer guide was accessible and confirms the narrow 12 V stop-start scope and the same default figures. Its visible conversation does not supply the source SLX or model-data guide, so it does not establish numerical parity with the original model.

The route is `/virtual-lab/hev/12v-micro-hybrid-stop-start/`; `static/js/micro-hybrid/model.mjs` exports `DEFAULTS`, `FIELDS` and the deterministic `calculateMicroHybridStopStart` function. All inputs are in the stated units; the JSON export carries model ID, inputs and named outputs. Results and temporary comparisons remain in the browser; they are not assessments or persistent server records.

The car and traffic light illustrate a decision sequence, not longitudinal vehicle physics. Playback summarises at most three stops while displaying scenario totals. Brake regeneration, 48 V assistance, emissions certification and battery ageing are outside this model. Suggested input ranges warn rather than clamp; finite and physically necessary denominators are checked. Final SOC is clamped to 0–100%. A null break-even indicates that the accessory fuel-equivalent rate is not lower than the idle rate.

Run model tests with `node --test tests/micro_hybrid/*.test.mjs`. Run the isolated browser tests with `.venv/bin/pytest -m e2e tests/e2e/test_micro_hybrid_ui.py`; see the project README for browser dependencies.
