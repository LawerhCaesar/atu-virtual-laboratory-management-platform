# Administrator Management Guide

Bless Kofi Atisu — ATU Virtual Laboratory Management Platform  
Updated: 14 September 2026  
Status: the controls described here are implemented and locally verified, not signed off for institutional deployment.

## Navigation

Sign in as an active Administrator and open `/dashboard/`. Students and Lecturers cannot access management views, including direct object URLs. Public registration never creates Administrators.

| Workspace | Path | Workflow |
| --- | --- | --- |
| Registration review | `/accounts/approvals/` | Approve/reject and complete academic setup before activation. |
| User management | `/accounts/manage/` | Search/filter, password recovery and eligible account suspension/reactivation. |
| Course allocation | `/academic/courses/`, `/academic/offerings/` | Create courses/offerings and allocate Lecturers/enrolled Students. |
| Resources | `/practicals/resources/` | Register, edit eligible resources, approve, disable, restore to draft, create revisions. |
| Notices | `/management/notices/` | Draft, preview, confirm delivery, cancel unsent drafts, review delivery/open counts. |
| Support inbox | `/management/support/` | Filter requests, respond, resolve/reopen and notify the account holder. |
| Settings | `/management/settings/` | Configure support email, hours and plain-text help guidance. |
| Reporting/audit | `/reports/`, `/reports/audit/` | Activity review and controlled CSV/PDF exports. |
| Academic hierarchy | `/django-admin/` | Existing restricted backend for faculties, departments, programmes and academic periods; staff permissions are additionally required. |
| Help | `/help/` | Public guidance/contacts and private active-account support history. |

Existing role assignments and academic-access rules are preserved. This increment does not introduce impersonation, public role escalation or automatic reassignment of a Student's submissions to a different role.

## Account access

Select Suspend or Reactivate, read the impact, supply a reason and tick confirmation. Suspension applies only to active academic accounts. Pending/rejected registrations cannot bypass approval through reactivation. Reactivation requires a suspended account with academic setup. Staff, superuser and Administrator accounts are excluded from this access-change workflow.

Both transitions rotate the session-authentication revision. Old sessions remain invalid even if an account is reactivated before an old browser makes another request. Fresh sign-in is required; existing password, submissions and course records remain unchanged. Actor and reason are audited. Never record passwords or private evidence in reasons.

Temporary-password recovery remains a separate audited workflow requiring replacement at first sign-in.

## Resource lifecycle

- New resources remain drafts until approved. Integration secrets remain in deployment configuration; the form stores only a key identifier.
- Editing an unused, non-archived resource clears approval and returns it to draft. Fresh approval is mandatory.
- Resources attached to a task, submission or integration session cannot be edited in place. Create a revision with a new, non-empty version label. It records its predecessor and starts in draft without changing existing task links or run records.
- Disabling requires a reason and explicit confirmation. It archives the resource without deleting task links, submissions, sessions or evidence. Launch, formal-submission and pending signed-return checks enforce current approval. Coordinate with the Lecturer when unfinished tasks are affected.
- Restoration returns the resource to draft for fresh approval; it does not automatically enable access.
- The resource view in the Django backend is read-only to prevent bypassing audited controls.

This history guard is not a complete immutable parameter/launch provenance snapshot. The remaining academic policy and traceability requirement is retained in the acceptance pack.

## Notices

Choose all active academic accounts, active Students, active Lecturers, or one eligible academic account. Saving creates an unsent draft. Preview shows current eligible count; sending rechecks active approval. Review title, message, audience and optional internal path before confirming. External/protocol-relative links and missing platform paths are rejected; ordinary permissions still apply to linked pages.

Delivery is in-platform, not email. Sending is transactional, locks the draft and enforces one delivery per notice/account. Repeat sends are rejected. An empty eligible audience makes no deliveries and leaves the draft unsent. Cancelled drafts and sent records are retained; sent notices are immutable through the interface. Send a separate correction if necessary.

“Opened” means a recipient followed the notification link, not proof of comprehension or learning.

## Support and settings

Active account holders submit platform support questions through Help and see only their own recent requests/responses. Anonymous visitors can read contact/guidance but cannot submit requests. Administrators review requests, save a response/status and notify the requester. This is a latest-response workflow, not a threaded helpdesk or validated research-feedback instrument.

Settings allow contact email, hours and plain-text guidance only. Security limits, passwords, signing secrets, HTTPS and database credentials are not editable here. Configured guidance and user text are HTML-escaped.

## Local verification and upgrade

- 54 management-focused automated tests cover role restrictions, targeted URLs, CSRF, resource approval/history, notice eligibility/replay/cancellation, internal links, support privacy and session revocation.
- The full automated suite passed 140 tests. The expanded browser suite passed 56 cases: six workflows and 50 accessibility/responsiveness scans at widths 1280 and 390.
- Fifty axe reports contain no detected violations; 24 incomplete colour-contrast findings require manual assessment.
- Before the three new migrations, SQLite was privately backed up to `backups/management-jl0iED/before-management.sqlite3`; integrity check returned `ok`.
- Before/after counts and digests match for existing User fields, PracticalSubmission, Assessment and EvidenceFile records. The new session revision column is deliberately excluded. No users were reseeded, working passwords reset or grades invented.
- Existing login sessions require fresh sign-in because authentication now includes the session revision.

See the [verification record](implementation-verification-record.md), [acceptance pack](acceptance-test-and-evaluation-pack.md) and [deployment/recovery runbook](deployment-and-recovery.md). Real PostgreSQL/container execution, TLS, operational safeguards, full recovery rehearsal, manual accessibility and approved participant evaluation remain separate release gates.
