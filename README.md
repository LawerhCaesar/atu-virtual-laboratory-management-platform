# ATU Virtual Laboratory Management Platform

This repository implements the approved web-based platform for managing automotive practical assessment and controlled access to approved demonstration resources.

## Implemented increments

The implemented platform slices include:

- public Student and Lecturer registration only;
- Pending Approval → Academic Setup → Active account states;
- administrator-only approval and academic setup;
- Faculty, Department, Programme and Academic Profile records;
- protected Administrator, Lecturer and Student dashboards;
- five-minute authenticated-session inactivity timeout;
- audit events for registration, approval, activation, sign-in, sign-out and timeout;
- a non-public management command for bootstrapping the first administrator;
- courses linked to departments;
- course offerings linked to programmes, academic years and semesters;
- explicit Lecturer teaching assignments and Student enrolments;
- controlled demonstration-resource registration and Administrator approval;
- Lecturer task drafting, editing and publication for assigned offerings only;
- structured task questions, instructions, evidence requirements, deadlines, marks and resubmission limits;
- Student access to published tasks only when actively enrolled;
- audit events for course setup, allocations, resource approval and task publication;
- structured submission drafts with resource/version, parameter, run/session and output records;
- protected PDF, PNG, JPEG, CSV and TXT evidence uploads, limited to 20 MB per file and 100 MB per submission;
- formal submission confirmation and controlled resubmission attempts;
- Lecturer evidence review, corrective feedback and draft assessment;
- controlled result release, with unreleased scores hidden from Students;
- in-platform notifications for new tasks, resubmission requests and released results;
- permission-checked evidence downloads with no public media route;
- Administrator reporting for account, course, task, submission and result activity;
- filterable audit review plus CSV exports for users, submissions and audit records;
- a printable PDF administrative summary with a development-data label in local mode;
- audited Administrator-issued temporary passwords, shown once and followed by forced password change;
- confirmed, audited suspension/reactivation of eligible academic accounts with old-session revocation;
- resource editing with renewed approval, history-preserving revisions and confirmed disable/restore controls;
- Administrator notice drafts, audience previews, transactional in-platform delivery and retained delivery history;
- private account-holder support requests, Administrator responses and configurable support/help details;
- controlled-link and signed-return integration modes for approved demonstration resources;
- short-lived, submission-bound return tokens, HMAC-SHA256 callback verification, replay prevention and payload-size limits;
- fail-closed production settings, explicitly trusted private proxy headers and private response cache controls;
- a non-root container, separate non-superuser application database role and private evidence permissions;
- reproducible local Bootstrap assets, isolated Playwright workflows and desktop/mobile axe checks;
- read-only database/evidence recovery probes and a deployment/backup/restore runbook.

## Local setup

The public homepage includes **Did you know?** above sign-in. It randomly
selects automotive educational excerpts from Wikipedia, with article attribution
and CC BY-SA 4.0 links, and rotates every 60 seconds while the page is visible.
Visitors can pause/resume or request another item. Topic selection stays within
the platform's automotive scope; recently displayed items are excluded where
possible, but this is random selection, not a promise of endlessly unique facts.
The same-origin `/learning/fact/` endpoint bounds upstream responses and timeouts,
allows no user-supplied source URLs or redirects, and shares a one-request-per-minute
upstream cooldown/cache. No API key is required. Source-checked DOE/AFDC backup
facts keep the card usable during outages; homepage rendering and sign-in never
wait for a provider request. No JavaScript still displays a sourced backup fact.
Browser tests mock the external source; unit tests verify caching, safe parsing
and failure recovery without third-party calls.

The authenticated **Virtual laboratory** entrance at `/virtual-lab/` starts
with a choice of ICE, BEV, FCEV, Hybrid (HEV) and Vehicle Dynamics (VD).
Each system has a separately branded model catalogue. ICE currently has one
active simulation: **Fuel Delivery Optimisation**, with its own inputs, animated
fuel-path schematic, deterministic fuel-trim/consumption calculations, plots,
baseline comparison and exports. See [fuel-delivery integration and source
verification](docs/fuel-delivery-integration.md).
BEV now includes **Regenerative and Friction Brake-Force Allocation (BrakeLab)**
at `/virtual-lab/brakelab/`, with eleven editable inputs, a pure operating-point
calculation, force/energy charts and an original illustrative braking vehicle.
See [BrakeLab integration and source limitations](docs/brakelab-integration.md).
Vehicle Dynamics includes **Wheel-Slip Control Using ABS and TCS** at
`/virtual-lab/vehicle-dynamics/wheel-slip-abs-tcs/`, with fixed-step simulation,
controller states, full-resolution exports and an illustrative vehicle.
See [wheel-slip integration and source limitations](docs/wheel-slip-integration.md).
Vehicle Dynamics also includes **Vehicle Steering Response** at
`/virtual-lab/vehicle-dynamics/steering-response/`, with a five-state RK4 bicycle
model, four plot groups, a recorded top-down trajectory, replay controls and an
eleven-signal export contract. See [steering-response implementation and verification](docs/steering-response.md).
HEV includes **12 V Micro-Hybrid Stop-Start**; see
[microhybrid integration](docs/micro-hybrid-stop-start.md).
The FCEV environment has no configured simulations or speculative launch links.

Registered simulation pages include an optional, non-blocking **Module guide**.
The guide opens on the first visit per account and browser, gives practical
input, interpretation and verification steps, and can be reopened at any time.
See [walkthrough maintenance](docs/module-walkthroughs.md) when adding a model.

**Engine Live Data Demonstration is temporarily withdrawn.** It is absent
from the catalogue and its former `/virtual-lab/engine-live-data/` route,
including `?view=` bookmarks, returns 404. Its source, equations, templates,
3D assets and historical UI tests are retained for possible restoration;
the pure model/controller tests still run. See the [archived integration and
restoration notes](docs/engine-live-data-integration.md).

For online QA using Render and Supabase, see [Render staging deployment](docs/render-staging.md).

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py bootstrap_admin \
  --email admin@example.edu \
  --full-name "Platform Administrator"
.venv/bin/python manage.py runserver
```

The application uses SQLite when `POSTGRES_HOST` is unset, which keeps local checks lightweight. Copy `.env.example` to `.env` and run `docker compose up --build` for the PostgreSQL deployment profile.

The Compose command above is the **local development** profile. For staging/production, use the standalone `compose.production.yaml` file and follow [`docs/deployment-and-recovery.md`](docs/deployment-and-recovery.md). Production refuses SQLite fallback and missing/default secrets.

Before registering users, create the Faculty, Department, Programme and Academic Year hierarchy in `/django-admin/`. The platform administrator approval queue is at `/accounts/approvals/`; course and offering management, account recovery, reports and audit review are available from the Administrator dashboard.

## Signed demonstration-resource return

Keep integration secrets outside the database in `INTEGRATION_SHARED_SECRETS`, then register the matching key identifier on an approved resource configured for **Signed return**. The platform never adds a shared secret or student identity to the launch URL. The callback contract and signing procedure are documented in [`docs/signed-integration-return.md`](docs/signed-integration-return.md).

For local interface review, an idempotent command creates clearly labelled demonstration accounts, one offering, one approved resource, one published task, one unsubmitted draft and one submission awaiting review. It does not create grades or results:

```bash
.venv/bin/python manage.py seed_demo_data
```

The command prints the local-only demonstration credentials. It refuses to run when `DJANGO_DEBUG=false`.

## Verification

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/pytest
```

For isolated browser/accessibility tests, install the pinned Node packages with `pnpm install --frozen-lockfile --ignore-scripts`, run `pnpm run sync-assets`, install Chromium with `.venv/bin/python -m playwright install chromium`, then run `.venv/bin/pytest -m e2e tests/e2e -q`. The ordinary test command excludes browser tests. All browser grades/password resets are synthetic test-database activity, not changes to the working database.

The first administrator is forced to replace the bootstrap password before opening any protected platform page.
The bootstrap command prompts twice in a private interactive terminal when no password is supplied; this keeps it out of shell history. Non-interactive setup can use a securely injected `ATU_ADMIN_PASSWORD` with `--no-input`.

## Current development boundary

The functional core and production-hardening implementation are present. Release still requires a passing PostgreSQL/container CI run, real staging TLS/reverse-proxy checks, backup/restore rehearsal and manual accessibility/user acceptance. The CI configuration alone is not a passed run. Demonstration data and automated fixture assertions are not evidence of research findings or system-performance results.

See the [implementation verification record](docs/implementation-verification-record.md) for observed local results and remaining gates, and the [acceptance/evaluation pack](docs/acceptance-test-and-evaluation-pack.md) for objective traceability, UAT cases and genuine-data collection forms. The pack explicitly records outstanding approved requirements rather than assuming the current implementation is complete.

The [Administrator management guide](docs/administrator-management-guide.md) explains the completed controls, resource-history rules, notice delivery and local database upgrade. Start from `/dashboard/` after signing in as an active Administrator.
