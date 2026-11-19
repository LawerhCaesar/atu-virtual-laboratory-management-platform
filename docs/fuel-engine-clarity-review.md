# Fuel Delivery and Engine Live Data correction review

16 November 2026. Isolated review copy of repository commit `05d72ec5a4a626f35060b7ab0b334eed799b5b66`. No upstream push or deployment. The two supplied Platform Correction instruction files have identical SHA-256; they constitute one Engine Live Data brief.

## Fuel Delivery Optimisation

The numerical model, bounds, integration order, eight-value vector and reset/resume behavior are unchanged. Current preview now states whether its inputs differ from the latest recorded sample. The analysis section identifies Last recorded run, its original per-sample settings and input segments. JSON adds explicit contexts and a run ID while retaining the prior top-level fields and full history; CSV column order and values are unchanged. Top-level JSON inputs/outputs are explicitly labelled as the current preview.

Fresh comparison still solves two fresh, complete runs from zero learned trim/cumulative fuel, with the current inputs and scale as the only difference. The interface separately displays adjusted-minus-baseline cumulative fuel change. Each result's Fuel saving remains the corrected operating baseline before trims, scale and injector bias; it is not the completed-run comparison percentage.

The action is now Apply suggested scale to test. Adjacent wording gives measured lambda / target lambda bounded to 0.85–1.05, explains that it does not compensate for STFT/LTFT/bias already applied, and retains the current mixture warning. Duty wording shows requested duty, the 100% display cap, theoretical fuel demand and infeasibility above capacity. Vehicle illustrations remain separate from the generic four-cylinder fuel model.

A final clock-rebase stress check exposed negative elapsed time in the existing presentation clock, which could send a negative path phase to the 3D renderer. Visual frame elapsed is now clamped at zero; this does not change calculation time, state integration or model outputs.

Five supplied numerical acceptance cases pass within their stated precision, including the rich-reading trim case and saturated high-load case. Full expected/observed input/output records are in `review-evidence/fuel-acceptance.json`. The source-derived SLX expression/wiring regression also passes; no MATLAB solver run is claimed. The original external SLX was not edited.

## Engine Live Data Demonstration

Pause previously registered `pause` directly as its click listener. The event object became the status text. This was reproduced in a real headless Chrome session before the patch and captured in `engine-pause-before.png`. The listener now supplies a plain string; the helper also rejects non-string status objects. Browser tests verify paused time, resume continuity and one-sample Step behavior.

Visible scope, accessible help names and both guides use simulated authorisation and virtual electric-water-pump duty. Internal identifiers remain compatible. The process indicator is Start request accepted, reflecting the momentary SafeStartCondition rather than a continuing permission latch.

CSV remains the same 46-column accepted-input/output sample stream, capped at the latest 60 seconds / 1201 rows. The additional evidence-package JSON contains the identical CSV, signal dictionary, fixed 0.05 s interval, actual source hashes, case/run identifiers, UTC export time, retained/total sample counts, first/last times, transition events and explicit cap warnings. Pending inputs are separate from recorded accepted values. The source identifier is calculated from actual local reference/controller bytes; it is not asserted to be a production release hash.

## Timing source decision

The approved EngineLab programmer guide explicitly states: "State elapsed accumulates in floating point; do not round it or introduce epsilon thresholds." It also requires adding 0.05 before evaluating one transition and preserving branch order. The current reference and embedded master-prompt source implement that convention. Accordingly, this correction does not change the reference controller or add tick rounding/tolerance.

| State entered at local tick 0 | Nominal threshold | Immediately before nominal threshold | At nominal threshold tick | Observed transition tick |
| --- | --- | --- | --- | --- |
| PRIME | 2.0 s | Tick 39 remains PRIME | Tick 40 enters CRANK, elapsed resets to 0 | 40 / 2.00 s |
| CRANK, imposed RPM 200 | 5.0 s | Tick 99 remains CRANK | Tick 100 remains CRANK; accumulated elapsed is slightly below 5 | 101 / 5.05 s |
| SHUTDOWN | 0.5 s | Tick 9 remains SHUTDOWN | Tick 10 remains SHUTDOWN; accumulated elapsed is slightly below 0.5 | 11 / 0.55 s |

Tests include samples before, at and after each transition and emergency/stop/ignition-off precedence in PRIME, CRANK and RUN. The eleven supplied numerical anchors, including isolated ECT disagreement and the accepted battery cap, pass. Expected/observed data are in `engine-acceptance.json`.

At the 16 November review, the canonical EngineLab SLX and current Kofi Frempong chapter equations were not found in the accessible supplied files. The shared discussion link could not be fetched. Thus **native Stateflow equivalence remains unverified**. Retaining the explicitly approved written floating-point convention is not proof that the SLX intentionally has the same one-sample behavior. Recover the canonical source and compare before authorizing a timer-semantics change. No SLX was modified.

## Evidence limits

At the 16 November review, the five named November 15 CSVs, observations.json, original screenshots and Fuel Delivery review JSON cases were not supplied/found. Their reported sample counts are retained only as statements in the briefs; they were not revalidated or reconstructed. New browser screenshots/exports are dated correction evidence, never replacements for the missing original records. Overlapping retained windows are not summed as independent observations.

Tests demonstrate this educational web implementation. They do not establish OEM calibration, measured fuel economy, emissions compliance, physical-engine/pump performance, biometric recognition, combustion validation or student learning gains. Authentication, roles and unrelated modules are unchanged.


## Update on 19 November 2026

The user supplied EngineLab_Model_and_Evidence.zip with the canonical Engine_Live_Data_Demonstration.slx, all five original CSVs, observations, original screenshots and the guides. These are preserved unchanged under review-evidence/supplied-2026-11-19. canonical-engine-source.json records the SLX SHA-256, solver settings, extracted embedded MATLAB-function code and hashes of every supplied file.

The saved fixed step is 0.05 s. The embedded start_run source adds 0.05 to a persistent double elapsed variable before testing >=2.0, >=5.0 and >=0.5, resets elapsed on transition, and gives emergency/stop/ignition-off precedence before RPM/timeout. This agrees with the browser reference and the approved handover. Keep the original numerical engine; the 40/101/11-tick convention is supported by the canonical source. This closes the missing-source investigation; no timing calibration change is required.

Every calculated output and continuing transition sample in each of the five supplied CSVs matches the reference under the documented source/state comparison (maximum absolute difference 0). The two zero-origin runs also pass complete deterministic replay from the initial state, without injecting recorded state. The first sample of a retained nonzero-origin window checks algebra only because its preceding state is not supplied. Comparison details are in supplied-engine-comparison.json. These checks are not an execution of the MATLAB/Simulink solver.

Files 09/10 share 693 identical samples and 10/11 share 147 identical samples. They are not summed as independent observations. No original CSV, image or SLX was changed. The canonical source and original browser evidence now support the timing explanation, while a new MATLAB solver run and the current thesis chapter equations remain outside the verified evidence.
