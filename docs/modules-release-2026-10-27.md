# Fuel Delivery and BrakeLab release checks

This release combines the Fuel Delivery completeness-audit fixes with the new
BEV BrakeLab module authorised from its supplied programmer guide and prompt.
Both follow the existing Django/Bootstrap/ES-module architecture. The existing
Render staging service, database settings, persistent evidence storage and
authentication rules are unchanged. Engine Live Data remains withdrawn.

## Scope and sources

Fuel Delivery's equations, defaults and exact eight-value integration order are
preserved. Its source-graph checks still match the inspected SLX fixture. Runtime
calculation/comparison errors now stop playback and block stale export; shorter-
than-elapsed duration edits are rejected without relabelling history. Input
purposes, out-of-range nudges, cylinder-event cues, duty warning states, toolbar
placement, learning text and contract documentation are covered by regressions.
See [Fuel Delivery integration](fuel-delivery-integration.md).

BrakeLab implements the supplied canonical programming contract, 11 inputs,
15 fixed calibration values, all required outputs and visual aids, active-limit
diagnostics, force-balance checks, four chart groups and original SVG vehicle
playback. The document review guided explicit handling of normalisation,
W/kW units, zero-demand stop-estimate sentinels, the protected sub-1 N percentage
denominator and separation of playback from operating-point results. No actual
BrakeModel.slx or MATLAB numerical validation is claimed. See [BrakeLab
integration](brakelab-integration.md) for source hashes, decisions and limitations.

## Local results on 27 October 2026

| Check | Observed result |
|---|---|
| `pytest -q` | 198 passed (non-e2e suite; browser tests run separately). |
| Both module Node suites | 22 passed, including 2500 canonical-reference BrakeLab points and 8000 seeded Fuel calculation steps. |
| BrakeLab, Fuel and system-navigation Playwright suites | Clean final run: 17 passed, plus 2 separately passed 768 px tablet cases; axe and reduced-motion checks included. |
| `manage.py check` | No issues. |
| `makemigrations --check --dry-run` | No changes detected. |
| Render-profile `collectstatic` | Passed; new assets collected and post-processed. |
| JavaScript syntax and `git diff --check` | Passed. |
| Manual screenshot review | Desktop/mobile vehicle, fuel path, duty warning and BrakeLab analysis layouts inspected. |

The first combined browser run exposed an incorrect test setup: its intended
overflow input still used a tiny demand and therefore correctly remained finite.
The setup was corrected to request full demand before applying extreme mass.
The targeted rerun and subsequent clean 17-test release run both passed.

Screenshots/traces are local QA artifacts under `test-results/`, excluded from
the repository. The canonical reference fixture is committed so CI can repeat
the source-contract checks without personal Downloads or MATLAB access.

## Deployment gate

Deployment is to the existing `atu-virtual-laboratory-staging` Render service,
not a new paid service. Automatic deploys remain off. Publish the tested commit,
require the full GitHub PostgreSQL/browser/container workflow to pass, and then
deploy that commit through authorised Render access. Confirm the actual deployed
commit, readiness endpoint, static assets and protected module routes afterward.
No deployment is implied by this local verification record.

No schema migration is introduced by this release. Do not copy local demo users,
SQLite data, secrets or synthetic test flags into staging. The educational
limitations, unavailable source-model verification and need for later real-user/
real-device evaluation remain visible after deployment.
