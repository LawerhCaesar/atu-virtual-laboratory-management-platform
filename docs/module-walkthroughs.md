# Simulation walkthroughs

The shared guide opens on the first visit to a registered simulation for each signed-in account in the current browser. It is an optional non-modal panel: it never runs a simulation, changes inputs, exports results, or submits assessment work. The always-available Module guide button reopens it; Show me scrolls to and highlights the referenced control. Back, Next, Finish later, close, and Escape support navigation. Finishing returns the next manual opening to step one.

Progress and whether the guide has been shown are stored in browser local storage under a key scoped to the account, module route and guide version. Progress is device/browser-specific, not a server-side record. If storage is unavailable, the guide still works within the current page but may reappear on the next visit.

## Adding a module

Register its route and title in `SYSTEM_MODELS` in `apps/core/laboratory.py` and extend the normal `base.html`. The shared context processor then supplies the walkthrough automatically, including a conservative general guide if no tailored guide exists. Add a specific entry keyed by the namespaced route to `static/js/walkthrough/steps.mjs` before considering the module's onboarding complete. Each step has a stage, title, description, tip, check and optional target CSS selector. Use stable selectors, state units and expected values, describe how to set up a repeatable test, and distinguish model checks from physical validation. Avoid directing the guide to perform actions automatically.

The three current modules have tailored guides. The withdrawn Engine Live Data Demonstration has a retained guide ready if its route is registered in the catalogue again; the guide does not restore its route. New models that bypass the catalogue or the shared base template need explicit integration before they can receive the guide.

## Verification

`tests/test_walkthrough.py` covers catalogue registration and role-scoped rendering; `tests/e2e/test_walkthrough_ui.py` covers first visits, reopening, progress, separate users/modules, storage failure, responsive layout and accessibility. Continue to run the existing module browser suites because the guide is rendered on their pages.
