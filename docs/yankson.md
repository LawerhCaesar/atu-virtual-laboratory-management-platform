# Yankson authenticated starting laboratory

Route `/virtual-lab/ice/authenticated-engine-starting/`, under ICE. Student: Emmanuel Yankson Sackey; supervisor: Dr. Peter Nyanor. Shared student profile and first-visit/reopenable walkthrough are included. Missing biography and portrait retain placeholders.

The uploaded Markdown and programmer PDF are retained under `docs/reference/yankson/`. The executable block is extracted byte-identically to `static/js/yankson/engine.js`, SHA256 `7e34037a0d2c797f9594d8a9cca8dcb43ca1e8f60336bac74da27dfdb1360279`. The pure controller is unchanged. UI code is an external classic-script adapter using the existing Django role policy, styling and static build. There are no new packages, migrations, microphone permissions, biometric APIs or actuator endpoints.

The 0.01 s accumulator retains time debt and limits work to 200 samples per frame. Pause/hidden page freezes model time; restart does not count hidden wall-clock time. Session workload caps at 30001 rows. Every input row is timestamped and retained with all 28 output columns. CSV exports raw results; JSON includes input history, parameters, events, simulated-interaction classification and explicit native/human-test limitations. Commands are unique sequence-numbered simulated events; stale capture time and wrong-command experiments use the reference checks. Contacts re-arm only after release. The engine retains the original one-sample actuation delay, 3 s crank deadline, 10 s permission epoch, fresh voice limit and distinct starter/run supply signals.

Controls cover automatic short/long contacts, failed match, explicit finger-down/release, fresh/stale/wrong command, emergency stop, controller recovery, full reset, independent power/interlock/monitor/ignition settings, CAN ID/length/range/drop experiments, additional resisting load and RPM override. Every identity/device input is labelled simulated. The chart plots CAN and plant RPM with a 20 s display window; exported data are neither clipped nor decimated. Supporting equation explanations and full telemetry appear beside the event history. No human recognition-accuracy rates are inferred from control scenarios.

The 10-page PDF was fully text-extracted, including parameter tables, signal contracts and five external technical references. MathWorks Stateflow programmatic API, model appearance and convertToSTT pages were accessible; Microsoft SpeechRecognitionEngine and WinBioVerify pages returned technical content with authorization notices. They describe native implementation context rather than browser device support. The SLX and user PDF were not present in Downloads. Consequently the historical 33-case/52833-sample native comparison cannot be repeated. The source's built-in 10 checks pass; they are not equivalent to rerunning all 316 native assertions. Original native CSVs must never be generated from this JavaScript as a substitute for independent evidence.

Repeat: `node static/js/yankson/engine.js --self-test`, `pytest tests/test_yankson.py`, and `PLAYWRIGHT_BROWSERS_PATH=/private/tmp/atu-playwright pytest -m e2e tests/e2e/test_yankson_ui.py`. Browser acceptance checks exercise both starting routes, stale voice, pause, exports, emergency stop/recovery, ignition-disabled timeout, responsive overflow and axe WCAG. Screenshots are generated under `test-results/yankson/`. Real hardware and human voice/fingerprint trials remain not performed.

## Practical follow-up — isolated review revision, 30 October 2026

This revision is intentionally local only. Do not push or deploy it without a separate instruction. Baseline commit: d28182833acf9d4d451d01d8205c0a93e3c6e976. `engine.js` retains its original SHA-256; the equation and model interfaces remain unchanged. The new `practical.js` adapter uses the browser speech API if supported, pointer/keyboard contacts and explicit simulated identity. It does not install a bridge, create WebAuthn credentials, connect a fingerprint reader, claim a biometric match or address a physical relay.

### Operation

Open the existing module route in the local review copy. Use Check this device, explicitly select Practice identity, then hold the contact target using touch/pointer/Space/Enter. Short release grants voice permission; a long hold generates one direct request. Microphone listening requires current permission, foreground normal-time execution at 1×, and a deliberate Listen action. Browser recognition can use a remote service; no offline claim or raw audio storage is made. Save a personalized full phrase or restore Hey Start. Preference storage is namespaced by the authenticated user ID; if storage fails, the current visit remains usable.

Speech results are final-only, consumed once and bound to experiment generation, authorization epoch, command and cancellation token. Reset, stop, pause, command changes, circuit edits, new authorization, page hide or navigation invalidate pending requests. Complete phrases use Unicode normalization, case folding, punctuation-to-space replacement and whitespace collapse. `do not hey start` does not match `Hey Start`. Permission, missing-microphone, no-speech, network and service errors remain failures. Automated tests use a synthetic SpeechRecognition adapter; no human microphone or real reader trial has been performed.

Pointer capture supports release outside the target. Lost capture, cancellation, focus loss and hidden-page interruptions fail the unfinished contact. Keyboard repeat cannot create new holds. Measured wall duration, contact source, practice-identity label and model timing are exported. The reference remains sampled at 10 ms, so model contact timing is quantized. Live inputs are refused under accelerated simulation pacing; the original simulated test controls remain in a separate drawer. Pausing freezes model time, and pending time debt is not discarded or converted to a larger physics step.

### Circuit and parameters

The workbench labels the Toyota 1NZ/starter, ESP32-WROOM-32, R503, voice command source, protected relay drivers and suppression, separate run supply, battery/fuse/regulator, shared reference, interlocks and SN65HVD230/ECU CAN pair. All terminals are functional labels: no unverified 121-pin assignment is invented. The exact usEFI/uaEFI board revision and purchased DFRobot voice-module model remain to be confirmed. An R503 device is not shown as connected. No unsupported hardware adapter returns a fabricated success.

Connected/disconnected toggles are explicit functional terminal pairs, with keyboard/focus and hover explanations. Open power maps to powerGood=0; common-reference/interlock opens map to interlockOK=0 as a labelled teaching preflight. Missing contact/match/voice paths gate those inputs. CANH/CANL or controller/transceiver disconnects map to CANdrop. Run-path loss disables virtual ignition. Starter-path loss uses a disclosed teaching equivalent (ignition disabled plus extra opposing load); it does not calculate relay/solenoid circuitry or change the core relay output. Protected-driver drawing never connects GPIO directly to a coil. The circuit is not an analog, impedance, EMC or safety validation.

Editable bounded teaching controls cover short/long contact thresholds, authorization/crank duration, running/stopped RPM, qualification, CAN period/freshness and voice event age. Core validation remains authoritative and Ts stays 0.01 s. Valid apply starts a new experiment; pending devices are cancelled, old permission is discarded, and labels/countdowns update from the actual parameter array. Invalid edits preserve the prior experiment. Known-good wiring and parameter-default resets are separate actions.

Guided experiments cover missing/stale/malformed RPM, brief versus qualified speed, ignition failure, CAN loss after crank acceptance, monitor loss and supply/interlock faults. They distinguish expected from observed effects rather than automatically claiming every hardware scenario passed. CAN validity is independent of identity and cryptographic authenticity.

### Review files and testing

Changed runtime files: `static/js/yankson/ui.js`, new `static/js/yankson/practical.js`, `static/css/yankson.css`, `templates/core/yankson.html` and `static/js/walkthrough/steps.mjs`. Documentation and browser tests accompany them. JSON retains all 18 model inputs and 28 outputs, selected parameters, circuit state, input sources and reason events; CSV retains the original raw output columns.

Technical references reviewed: W3C WebAuthn Level 3, MDN SpeechRecognition, DFRobot SEN0539 documentation (candidate module, not confirmation of purchased hardware) and TI SN65HVD230 datasheet. TI documents 3.3 V operation; the workbench labels this without calculating electrical behaviour. These sources do not supply a supported local fingerprint contact bridge.

Local preview procedure (from the isolated checkout): install existing requirements in a virtualenv, run `python manage.py migrate`, `python manage.py seed_demo_data`, then `python manage.py runserver 127.0.0.1:8877 --noreload`. Synthetic student login: `student@atu-demo.local` / `DemoPass!742`. Never seed demo records into staging. Existing local runtime may be reused without copying credentials or production data.

Verification commands:

```
node static/js/yankson/engine.js --self-test
pytest tests/test_yankson.py -q
PLAYWRIGHT_BROWSERS_PATH=/private/tmp/atu-playwright pytest tests/e2e/test_yankson_ui.py tests/e2e/test_yankson_practical.py -m e2e -q
python manage.py check --settings=config.build_settings
```

Synthetic-adapter tests are interface tests, not human speech accuracy or native MATLAB parity. Native CSVs remain unavailable. The archived implementation specification is provenance; this section documents the revised behavior and limitations.
