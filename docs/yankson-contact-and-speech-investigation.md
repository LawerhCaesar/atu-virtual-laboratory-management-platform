# Contact and speech investigation — 22 November 2026

The owner first reported that contact did not grant permission, then clarified that Start was not being recorded or recognized. The exact owner-side service status and a fresh export have not yet been supplied. The cause is not established, and no human speech success is claimed.

## Changes

- Step 1 now exposes the existing phrase-only diagnostic as **Test spoken command**, with no contact or practice-identity prerequisite. It uses the actual browser recognition service when the owner operates it; it cannot authorize or start the engine.
- The target/transcript/match or browser error is visible in Listen and observe. Testing a phrase no longer forces open technical CAN diagnostics.
- Basic identity guidance reflects selected Practice identity instead of telling the owner to re-verify a physical device. The original device-authentication status remains under Advanced device settings. Device security and identity policy are unchanged.
- The guide and walkthrough explain capture versus recognition and where to reach the voice-only check.

## Contact reproduction

Six automated mouse holds with an ordinary advancing browser clock (no fake-clock stepping) granted permission: three at 1440 px and three at 390 px. The first reproduction run passed both parameterized tests in 13.39 s. Measured durations were approximately 0.508–0.512 s; sampled model durations were 0.49–0.50 s. These are software reproduction observations on the local machine, not owner-operated holds or evidence of human speech recognition. Saved observations are in `test-results/yankson-contact-investigation/real-clock-1440.json` and `real-clock-390.json`.

The contact complaint was not reproduced in those attempts. No timing rule, permission window, interlock or supervisor equation was relaxed to manufacture success.

## Required next observation

The owner was asked to save any existing run, refresh the local page, click Test spoken command, allow the microphone, say Start and report the exact status/transcript. This isolates capture/recognition from contact authorization. A moving waveform alone proves capture, not recognition. A phrase-only match proves the diagnostic recognized text, not that an authorized engine-start sequence succeeded.

Current human acceptance: **BLOCKED pending the owner's actual status/transcript/export**. No synthetic voice or automated callback is presented as human evidence. All work remains local; no upstream push or deployment.

Final diagnostic/UI regression run: **19 passed in 78.28 s**. This includes six further normally timed mouse holds, the visible phrase-only MATCH and network-error paths (mocked callbacks), accessibility, reset, cancellation, layout persistence, old-phrase rejection and custom phrase activation. Latest measured mouse holds span 0.5095–0.5130 s. All six granted permission. Human recognition is still unverified; the owner-side failure is not claimed fixed. The updated 11-page guide was rendered and visually checked.
