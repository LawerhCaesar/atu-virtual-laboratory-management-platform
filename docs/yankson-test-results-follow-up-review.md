# Yankson follow-up with owner test results — local review

This continues the earlier local UI review on `codex/yankson-ui-follow-up`, based on `f87ed124198628c9d33f77cc418086f17fbc1ffd`. The source is `/Users/caesar/Downloads/Yankson_Codex_Follow_Up_With_Test_Results.txt`, SHA-256 `98d029fc8701769283ce9f3db6bb722354968305ef130a519090b47c0c4f786c`. No upstream push or deployment is authorized by this brief, and none was performed.

## Corrections

The existing three-step layout, left/right input/output separation, collapsible/resizable input pane, collapsed advanced sections and layout-only persistence are retained. This follow-up additionally:

- Opens and brings the microphone waveform into the viewport when Test microphone is selected. Narrow screens have a return link to the microphone controls to stop capture. Selecting Listen brings the latest feedback into view.
- Shows a blocked Listen reason and next action beside the button. After a direct start, it explicitly calls for reset and a fresh short contact before a new voice attempt.
- Exports measured contact duration, sampled model duration, model advance, their difference, pending scheduled time at press/release and the integration step. This gives timing investigation evidence rather than calling every difference rounding.
- Observes one-step start-source/long-contact events on every controller tick, before display-frame batching can hide them. No authentication permission is created by this observer.
- Keeps reported November 17, 20 and 21 evidence separate from active-run events. The learning guide explains the historical export's contradictory static wording without rewriting that original.
- Describes the study as virtual-only in new exports. The legacy `physicalObjective` field now says `OUTSIDE VIRTUAL STUDY SCOPE`. Previously saved exports are not edited. Stand images remain future concepts.

The downloadable 11-page guide was regenerated and all rendered pages were visually inspected. The controller `engine.js`, authentication backend, circuit constraints and supervisor equations remain unchanged. Engine SHA-256 remains `7e34037a0d2c797f9594d8a9cca8dcb43ca1e8f60336bac74da27dfdb1360279`.

## Owner-supplied evidence: what it establishes

These are statements from the attachment, not independently reprocessed raw traces. The Windows raw archive was not available in this local Mac workspace.

| Date | Reported observation | Interpretation |
|---|---|---|
| 17 November | Practice identity; 1.0367 s measured contact, 1.04 s model contact; transcript `hey start`; accepted voice and CRANKING at 10.34 s; RUNNING at 12.03 s; starter released, run supply retained; 11,669 rows, 28 columns | Historical successful human default-command demonstration used for thesis evidence. Not population recognition accuracy or a fresh acceptance trial. |
| 20 November | Reset exports isolated one current row, no practical/teaching events or trials, distinct run IDs; stale visible contact duration; Start Engine phrase-only diagnostic matched without crank | Preserve record isolation; fix stale timer. Diagnostic match is not personalized engine-start evidence. |
| 21 November | Owner confirmed waveform moved with speech at 48,000 samples/s. Short contacts granted authorization. A 1.7782 s measured long mouse contact, 1.61 s model contact, caused CRANKING at 12.08 s and RUNNING at 13.77 s, approximately 750 RPM, CAN VALID, starter OFF and run supply ON | Capture and direct virtual starting were demonstrated. No hardware fingerprint was tested. |
| 21 November | Voice source none, no recognition evidence, no accepted voice across 16,347 rows, recognition NOT RUN; Listen afterward lacked permission at 17.62, 21.28 and 26.59 s | Voice retest was not completed. This is neither a successful voice-start test nor proof of a defective recognizer. |

The reported 21 November run ID is `28c052cf-4a54-4c90-9a8b-7dd9784e496a`; reported raw SHA-256 is `8e35b2b21837ca93c0b6814e7ba47e92b036754136e8dab331a86c705485023b`. The original 17 November export reportedly says human trials were not performed despite its recorded recognition and accepted event. That contradiction is documented separately; no original evidence file is overwritten.

## Timing investigation

The reported measured/model long-contact difference is **0.1682 s**. That exceeds one 0.01 s model step and must not be described as ordinary display rounding. Without the original raw trace, event-loop timing and machine conditions, the exact cause of that historical gap remains unconfirmed.

Source inspection shows that wall duration uses the established `performance.now()` source. The model advances through a requestAnimationFrame-driven fixed-step accumulator, plus immediate samples for input edges. Queued simulation time, rendering/event-loop delays and input sample phase can therefore contribute to measured/model differences. The new event diagnostics expose these quantities without forcing wall duration into the validated model or weakening interlocks.

Deterministic native input tests distinguish a **release edge** from a **still-held sample**. With default thresholds:

| Contact duration at release | Native short events | Native long events | Native start requests |
|---|---|---|---|
| 0.14 s | 0 | 0 | 0 |
| 0.15 s | 1 | 0 | 0 |
| 1.49 s | 1 | 0 | 0 |
| 1.50 s | 0 | 0 | 0 |
| 1.51 s | 0 | 1 | 1 |

A still-held sample at 1.50 s fires the long event once. Release exactly at 1.50 s satisfies neither the short-release rule nor the still-held long rule in the unchanged engine. This is edge-order semantics, not rounding. The displayed measured classification must be read alongside the actual sampled-controller decision. The supplied original MATLAB input/trace pairs remain unavailable for a fresh independent parity run; no new parity claim is made.

## Acceptance artifacts

Each new automated acceptance case saves configuration, source, expected response, observed response and PASS/FAIL in `test-results/yankson-test-results-follow-up/`. Human-only cases are listed separately as BLOCKED until an operator performs them. Browser speech callbacks are mocks, never substituted for human speech.

The files include `UI-01-software.json`, `UI-02.json`, `TOUCH-01-software.json`, `TOUCH-02-native.json`, `RESET-01.json`, `VOICE-02-software.json` and `REG-01.json`, plus basic/expanded screenshots and separate prior/current reset records. Existing UI tests additionally cover 390-pixel layout, accessibility, mouse/keyboard resizing, collapse, reload without authorization persistence, measured boundaries, cancellation/lost focus, sustained one-shot holding and mocked voice-source behavior.

Final execution results and the case summary are appended after testing. No unperformed owner interaction is classified as passed.

## Pending owner acceptance

An actual spoken Hey Start test was requested from the owner during this review. No new transcript, exported trial or engine outcome has yet been received. UI-01's complete human workflow, TOUCH-01's owner-operated mouse hold and VOICE-01 remain BLOCKED for that evidence; software-only portions have separate records. Nonmatching human speech is also unperformed even when its mocked rejection regression passes.

The isolated local preview is `http://127.0.0.1:8897/virtual-lab/ice/authenticated-engine-starting/`. Demo login is `student@atu-demo.local` / `DemoPass!742`; it uses a temporary local SQLite database and synthetic accounts, not the live database. The live website has not been changed by this work.

For the voice trial: test capture and confirm the moving waveform, stop that test, keep Hey Start / en-US / 1× and healthy circuit/CAN settings, select practice identity, use a short 0.3–0.5 s contact and release, select Listen and speak Hey Start within permission. Record transcript, match, accepted voice, absence of a long-contact cause, CRANKING/RUNNING times and starter release. Retain failed/no-result attempts and export JSON before reset.

## Final actual results

- Broader browser regression run: **52 passed in 296.74 s**.
- Final UI acceptance run after the last edits: **20 passed in 101.53 s**, comprising the seven structured cases below and thirteen existing UI checks. These runs overlap; they are not 72 distinct tests.
- Relevant server tests: **6 passed in 0.74 s**. The unchanged native-engine hash/self-test is included in this server check.
- JavaScript syntax, Django system checks and whitespace checks passed. The isolated preview sign-in page returned HTTP 200. No live-site deployment was made.

| Case | Actual outcome | Status |
|---|---|---|
| UI-01 software | Mic action opens and reveals waveform on a 1366 × 768 viewport; one copy of each basic control; screenshots saved | PASS |
| UI-02 | Width 280 px at Home, 290 px after ArrowRight; 1366/390 px layouts unclipped; collapse/show retains outputs; Listen reveals decision; layout-only stored fields verified | PASS |
| TOUCH-01 software | Automated mouse hold advances and freezes timer; display agrees with measured event and separate timing diagnostics | PASS |
| TOUCH-02 native | Deterministic release/held boundary behavior matches the explicitly documented native edge rules, including the 1.50 s caveat | PASS (preservation check) |
| RESET-01 | New run ID, one current row, cleared timer/progress/permission/current events/trials; separate saved prior record and reported history retained | PASS |
| VOICE-02 software | Missing/expired permission and mocked nonmatching phrase cannot start; after direct start, nearby guidance requests reset and short contact | PASS |
| REG-01 | Open match/contact paths and invalid CAN inhibit starts; CAN loss faults at exactly 3.00 s from original accepted crank; outputs off; emergency stop/reset preserved | PASS |
| UI-01 complete owner workflow | No new human workflow result supplied for this revised local interface | BLOCKED |
| TOUCH-01 owner-operated hold | Software mouse events checked; no new owner-operated hold/export supplied | BLOCKED |
| VOICE-01 actual spoken Hey Start | Requested; no new transcript/export/outcome received | BLOCKED |
| VOICE-02 actual nonmatching speech | Mocked rejection verified; new human nonmatch trial unperformed | BLOCKED |

One initial new test run stalled because its intentionally pending microphone stub was accidentally returned as a promise from the Playwright evaluation. The obsolete runner was terminated, the test stub was corrected, and the replacement runs passed. This was a test-harness interruption, not a measured speech-recognition failure; it is retained in the acceptance summary.

Screenshots: [basic laptop](/Users/caesar/Documents/ChatGPT/sackey/test-results/yankson-test-results-follow-up/basic-laptop.png), [expanded output](/Users/caesar/Documents/ChatGPT/sackey/test-results/yankson-test-results-follow-up/expanded-laptop.png), [expanded input settings](/Users/caesar/Documents/ChatGPT/sackey/test-results/yankson-test-results-follow-up/expanded-input-controls.png), [small screen](/Users/caesar/Documents/ChatGPT/sackey/test-results/yankson-ui-follow-up/default-390.png).

The [case summary](/Users/caesar/Documents/ChatGPT/sackey/test-results/yankson-test-results-follow-up/acceptance-summary.json) contains configuration, input sources, expected/observed outcomes and human-only blocked cases. The [local patch](/Users/caesar/Documents/ChatGPT/sackey/output/yankson-follow-up/yankson-local-changes.patch) includes this follow-up and the preceding uncommitted UI changes. The [review package](/Users/caesar/Documents/ChatGPT/sackey/output/yankson-follow-up/yankson-review-package.zip) includes the patch, changed-file list, report, screenshots, guide and acceptance artifacts.

## Owner command change — 22 November 2026

The owner changed the current default from Hey Start to **Start** (correcting an initial “star” typo). The command field, initial/restored default, workflow heading, walkthrough and current guidance now use Start. Matching still requires the complete normalized command and fresh authorization; Hey Start is no longer accepted as the default. Historical reported demonstrations and the preceding acceptance records remain unchanged and refer to their then-active phrase. A new human Start trial remains pending. Refresh the local page to load this change; no push/deployment was made.

Start-command verification: **18 browser checks passed in 93.04 s**, including accepting Start after contact authorization, rejecting the old Hey Start phrase, restoring the new default, fresh state on reload and existing custom-command/voice lifecycle controls. Speech callbacks in this run were mocked; this is not a human Start trial. The updated guide was rendered and visually checked across all 11 pages.
