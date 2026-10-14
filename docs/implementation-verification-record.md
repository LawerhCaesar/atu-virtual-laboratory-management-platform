# Implementation Verification Record

Project: ATU Virtual Laboratory Management Platform  
Student: Bless Kofi Atisu  
Compiled: 14 September 2026  
Scope: production hardening, acceptance/evaluation preparation and Administrator management completion.

## Observed local results

| Check | Observed outcome | Boundary |
| --- | --- | --- |
| Ordinary automated suite | **140 passed**, 56 browser cases excluded by the default marker. | Synthetic Django test records; local SQLite. Includes 54 management-focused tests. |
| Isolated Playwright suite | **56 passed**: six workflows and 50 desktop/mobile accessibility cases. | Installed Chrome channel, temporary test database/media; external resources blocked. Temporary localhost binding required a sandbox-approved retry. |
| Axe scans | **50 reports, zero detected violations.** | Twenty-five page/role combinations at widths 1280 and 390; not complete accessibility certification. |
| Direct interface checks | No page-level or form-container overflow; described-by references exist; welcome skip link moves keyboard focus to main content. | Covered pages/viewports only. |
| Django system check | No issues identified. | Does not establish deployment availability. |
| Migration consistency | No changes detected by `makemigrations --check --dry-run`. | Does not prove PostgreSQL migration execution. |
| Production settings check | `check --deploy --fail-level WARNING` passed with explicit synthetic configuration and HSTS subdomain/preload flags enabled. | Configuration check only; no actual PostgreSQL/TLS/proxy connection. Default HSTS scope flags deliberately remain off pending operator approval. |
| Static build | Manifest/compressed static collection completed, including vendored Bootstrap. | Local build; container build still needs CI/staging execution. |
| Source/configuration checks | Python compilation, database-role shell syntax and all three YAML files parsed successfully. Static production isolation/secret-separation assertions passed. | YAML parsing is not `docker compose config` or SQL execution. |
| Visual review | Representative desktop/mobile reports, mobile submission workspace and Lecturer review screenshots inspected. | Not a participant usability study or exhaustive device review. |
| Management visual review | Mobile resource-disabling confirmation and desktop notice preview inspected. | Covered management screens only. |
| Local database upgrade | Three new migrations applied after a private SQLite backup with successful integrity check; existing account/submission/assessment/evidence counts and digests unchanged. | The added session revision field is excluded from the digest comparison; this is not a PostgreSQL or complete media-restore rehearsal. |
| Local readiness probes | Database ready; one evidence reference checked, zero missing. | Local working database/media only. |

An earlier browser run emitted a Python escape-sequence warning; its literal was corrected to an equivalent raw string. The latest 140-test and 56-browser runs completed without reported warnings. Initial management-only warnings about a naive fixture timestamp and notice pagination ordering were also corrected before the final runs.

## Accessibility follow-up

The expanded scan outputs contain 24 incomplete colour-contrast findings requiring manual assessment. The final 50 reports contain no incomplete `aria-valid-attr-value` findings. Scrollable tables are keyboard-focusable, form sizing is consistent, and grading/correction feedback labels have distinct control identifiers. Mobile navigation now wraps to contain the additional Help link.

Reports and screenshots are generated under `test-results/accessibility/`; failure traces/screenshots are retained under `test-results/e2e/`. These directories are ignored by Git and can be generated again using the runbook commands. Retain the actual reports when recording an institutional review; do not substitute this summary for the raw evidence.

## Actual local environment versus configured target

| Component | Local observed version/state | Configured deployment target |
| --- | --- | --- |
| Python | 3.12.14 | Docker Python 3.13; container execution unverified locally. |
| Django | 5.2.17 | Django 5.2 LTS requirement range. |
| Database | SQLite for the local suites | PostgreSQL 18 image and disposable CI service. |
| Playwright | 1.62.0 | CI installs the matching bundled Chromium. |
| Browser | Installed Chrome channel, fresh isolated profile | Bundled Chromium in CI; broader browser/device review pending. |
| Bootstrap / axe-core | 5.3.8 / 4.11.0 | Exact Node dependency versions with lockfile. |
| ReportLab / pytest / PyYAML | 4.5.1 / 8.4.2 / 6.0.3 | Declared runtime/development ranges. |

Chapter Three's eventual actual-environment account should distinguish these observed versions from configured/unexecuted targets. No approved chapter was edited in this increment.

## Implemented safeguards and documentation

- Production configuration rejects absent/default secrets, non-explicit host settings, invalid limit values and SQLite fallback.
- The production configuration isolates Gunicorn behind the trusted TLS proxy, uses non-root application execution and separates bootstrap database credentials from the non-superuser application role.
- New evidence files/directories use restricted permissions; public media routing is denied and application downloads remain permission-checked.
- Private/recovery responses use no-store controls, exports are audited, and CSV formula guards cover leading whitespace/control characters.
- Signed returns reject malformed, expired, replayed, revoked-access and late confirmed-submission callbacks. Launch tokens expose no internal Student/submission identifiers and accepted payloads omit the plaintext return token.
- Read-only database and evidence-reference probes are supplied. A matched database/media backup and isolated restore procedure is documented, not executed.
- The acceptance pack maps all four approved objectives to existing and still-required evidence, with 17 proposed UAT cases, observation sheets, exploratory feedback items, defect/retest records and Chapter Four handoff guidance.
- Administrator management now includes confirmed account suspension/reactivation with session revocation, history-preserving resource edits/revisions/disable/restore, draft/preview/send/cancel notices, private support requests/responses and editable support/help settings. All new management routes enforce Administrator access and ordinary CSRF protection. Resource edits in the Django backend are disabled to prevent workflow bypass.
- Local migration preserved existing account and practical records. A private pre-migration database backup is retained; users must sign in again because session authentication now includes its revocation revision.

## Unverified and outstanding gates

**Not ready for institutional release.** Docker and PostgreSQL tools are unavailable locally. The PostgreSQL/container/least-privilege smoke workflow is configured but has not been run on a remote CI host by this task. SQL role initialization, actual container startup, reverse-proxy/TLS behaviour and database/media restore remain unverified.

The acceptance pack also records unimplemented approved-interface functions and incomplete resource/version/parameter-provenance requirements. Profile/photo editing, self-service forgot-password support, Lecturer assessment export, prototype fidelity and other identified gaps must be implemented, explicitly limited or formally deferred with approval. Operational abuse throttling/monitoring, manual accessibility and real user acceptance remain release requirements.

No participant numbers, questionnaire responses, application response times, recovery times or learning-effect results are supplied. Tests did not alter the working database's grades or reset its users' passwords.

## Related files

- [Deployment and recovery runbook](deployment-and-recovery.md)
- [Acceptance test and evaluation pack](acceptance-test-and-evaluation-pack.md)
- [Signed return contract](signed-integration-return.md)
- [Administrator management guide](administrator-management-guide.md)
- [CI workflow](../.github/workflows/verify.yaml)
