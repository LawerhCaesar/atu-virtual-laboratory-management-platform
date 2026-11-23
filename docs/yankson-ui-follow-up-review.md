# Yankson local UI review — 21 November 2026

Implemented the supplied UI follow-up in local branch `codex/yankson-ui-follow-up`, based on `f87ed124198628c9d33f77cc418086f17fbc1ffd`. No upstream push or deployment was made. The source brief is `/Users/caesar/Downloads/Yankson_Codex_UI_Follow_Up_247c1371c7f542cf92319928e0686a5d_1.txt`.

## Result

The default workspace now has three steps: Check microphone, Authorise by contact, Say “Hey Start”. The contact pad, numeric duration and Listen controls are grouped together. Inputs occupy an adjustable left pane; feedback, waveform and the future engine-stand concept occupy the right. Narrow screens stack the panes. Users can collapse inputs, drag the divider, use arrow keys/Shift+arrow/Home/End, or use the width slider. Only width and collapse preference are stored; old authorization and personalized commands are not restored.

Circuit/CAN diagnostics, calibration, simulated events, lecturer exercises, records and numerical outputs are under collapsed Advanced settings. The measured timer starts at zero, updates during contact, freezes on release and separately reports the wall-time classification and actual sampled-controller decision. Reset clears it and voice permission. Cancellation, lost focus, paused live voice permission and sustained-hold one-shot behavior are covered. The displayed start source distinguishes measured long contact, browser recognition and simulated test events.

Microphone capture remains distinct from speech recognition. The waveform proves capture, not recognized speech or authorization. Listen explains why it is unavailable. Optional phrase testing retains its diagnostics view. The downloadable 11-page learning guide and walkthrough reflect the revised layout. All guide pages were visually reviewed; the final revised version/date pages were rendered and checked again.

Stand imagery is labeled as a future concept. The on-screen obsolete physical-construction objective statement was removed. Historical evidence metadata was not rewritten. Thesis results remain tied to the previously recorded “Hey Start” demonstration.

## Verification

- 332 non-browser tests passed in the broad unit run.
- 6 relevant server tests passed again after the final UI edits.
- The broad affected browser run produced 74 passes and one failure: the optional phrase test did not reveal the signals panel. A small navigation listener fixes that failure; see the final targeted run below.
- The final targeted run passed all 14 cases in 55.64 seconds: the phrase-test regression plus all 13 new UI cases. Its exact result is retained in `test-results/yankson-ui-follow-up/evidence-logs/yankson-ui-follow-up-final-acceptance.log`.
- The new cases cover desktop and 390-pixel layouts, accessibility scans, measured release boundaries, blur/pointer cancellation/reset, one-shot direct starting, mocked recognition, source labeling, pause, mouse/keyboard resizing, collapse and layout-only restoration.
- The unchanged native engine self-test passes all 10 checks. `engine.js` SHA-256: `7e34037a0d2c797f9594d8a9cca8dcb43ca1e8f60336bac74da27dfdb1360279`.
- JavaScript syntax, Django system checks and whitespace checks pass. Authentication, controller equations, CAN and starter supervision were not rewritten.

## Measured boundaries and limitations

These are automated keyboard holds with a controlled browser clock, **not human speech trials**. The timer measures elapsed contact; the native engine separately samples at 0.01 s and retains its existing pacing. Exact wall thresholds can consequently differ from native classifications. The UI exposes both instead of pretending that a measured long hold necessarily sent a long request.

| Wall hold (ms) | Measured classification | Maximum sampled contact (s) | Long events | Start requests | Permission after release |
|---|---|---|---|---|---|
| 140 | Rejected | 0.12 | 0 | 0 | no |
| 150 | short contact | 0.13 | 0 | 0 | no |
| 1490 | short contact | 1.48 | 0 | 0 | yes |
| 1500 | long contact | 1.48 | 0 | 0 | yes |
| 1510 | long contact | 1.49 | 0 | 0 | yes |

A sustained 5-second hold produces one long event and direct start in the automated test. At 1.50 and 1.51 seconds in these runs, the native controller grants short-contact voice permission rather than issuing a long request. The final UI reports this distinction. Each boundary JSON retains its exact displayed controller decision. No new parity claim is made against the unavailable 33 original native input/trace pairs.

## Failed attempts retained

Earlier local runs are retained alongside the final log rather than discarded:

- Initial legacy tests could not reach controls moved under collapsed Advanced settings. Test navigation was adapted; the new tests independently verify those sections start collapsed.
- The first compact-layout check found excessive spacing between contact and Listen; layout spacing was reduced.
- In-hold animation-frame assertions were too strict (0.29 versus 0.30 s before release), and a state expectation omitted the existing numeric suffix. Those assertions were corrected; exact frozen-release durations remain checked.
- One intermediate test contained JavaScript `or` instead of `||`; the test syntax was fixed.
- Duplicate headings/empty original wrappers and a microphone-byte details selector were corrected.
- Initial engine-stand status was blank until the first sample. The existing status renderer now also runs at mount, without injecting a fake controller sample.
- The remaining broad-run phrase-test visibility failure was corrected with an explicit diagnostic-view action, then retested.

## Human speech acceptance still pending

No actual person speaking “Hey Start” has been observed in this local review. Automated recognition callbacks test software behavior only and are labeled as mocks in test sources. Real microphone permissions, speech-service availability, hardware fingerprint use and end-to-end human speech success remain device/operator acceptance checks. The prior recorded demonstration is separate evidence, not a new UI trial.

A local preview is available at `http://127.0.0.1:8897/virtual-lab/ice/authenticated-engine-starting/` while its server is running. It uses an isolated temporary SQLite database and synthetic demo accounts, not the live database. Local demo student login: `student@atu-demo.local` / `DemoPass!742`.

For the pending trial: check microphone capture, use a real verified identity or clearly labeled Practice identity, hold/release for 0.3–0.5 s, click Listen and speak “Hey Start”. Record final recognized words, language, rejection/service error if any, actual start source and engine outcome. Keep unsuccessful/no-result attempts and export JSON before reset. A human trial was requested during this review and has not yet been reported.

Desktop/mobile screenshots and boundary JSON are in `test-results/yankson-ui-follow-up/` (ignored local artifacts). The source, guide, tests and this report are local working-tree changes; no remote publication was performed.
