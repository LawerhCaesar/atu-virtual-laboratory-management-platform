# Acceptance Test and Evaluation Pack

Bless Kofi Atisu — MTech Automotive Engineering — Accra Technical University  
Project: ATU Virtual Laboratory Management Platform  
Prepared: 14 September 2026  
Status: proposed acceptance protocol; no participant sessions or user-evaluation results have been recorded.

## Purpose and boundary

This pack checks whether the implemented management platform supports the four approved objectives. It does not assess the scientific validity of automotive models, replace physical workshop training, or establish that student learning outcomes have improved. No changes are made here to the approved aim, objectives or thesis chapters.

Keep three evidence categories separate:

1. **Developer verification:** repeatable tests using synthetic records and temporary storage.
2. **Deployment verification:** PostgreSQL, containers, TLS, proxy, backup and restore checks on an approved isolated environment.
3. **User evaluation:** consented Administrator, Lecturer and Student walkthroughs using non-assessed example tasks.

Passing one category does not prove another. Test-run durations are not application response-time measurements. Synthetic scores/password resets are fixture activity, not academic or participant results.

## Objective-to-evidence matrix

The objective wording below is retained from the approved handover.

| Objective | Demonstration to observe | Existing developer evidence | Additional evidence needed |
| --- | --- | --- | --- |
| 1. To design a web-based system that allows lecturers to create, organise and manage automotive practical assessment tasks. | An assigned Lecturer drafts, edits and publishes a task with instructions, questions, deadline, evidence requirements and approved resources; another Lecturer cannot edit it. | `apps/practicals/tests/test_task_workflow.py`: task creation/publication, author permissions and offering/resource restrictions. | Lecturer walkthrough; task/instruction clarity review; suitable Lecturer assessment-export workflow. |
| 2. To develop a student interface through which practical questions can be accessed, attempted and submitted in a structured format. | An enrolled Student accesses a published task, saves a structured response/run record, attaches evidence, confirms submission and follows an authorised resubmission. | Submission, evidence, resubmission, ownership and result-privacy tests; browser submission/grade-release workflow. | Student walkthrough; keyboard/mobile review; completeness and wording of submission confirmation. |
| 3. To create a database system for storing practical questions, student responses, assessment records, approved demonstration files and practical-output data. | Related task, resource/version, submission, evidence, assessment, notifications and audit records remain consistent after reopening and recovery. | Model/hierarchy tests, protected evidence tests, reporting tests and a missing-evidence recovery-probe regression. | Actual PostgreSQL/container run; matched database/media backup and isolated restore rehearsal; record-count and representative-download comparison. |
| 4. To provide an integrated platform for accessing approved simulations, demonstrations or practical concepts that can support automotive practical learning. | A permitted Student opens an approved resource; a capable resource returns signed outputs to the correct editable draft; invalid/expired/replayed/late returns are rejected. | Signed-return, malformed payload, token expiry, replay, revoked-access and confirmed-submission tests. | End-to-end staging test with an actual approved resource; approved parameter-range instructions; resource-quality/scope review by the responsible academic reviewer. |

The existing tests verify selected behaviours. They do not, by themselves, establish full objective achievement.

## Entry conditions

- Supervisor review of this protocol and the intended release scope.
- A passing PostgreSQL/container CI run and an isolated staging environment; do not use live grades or a real course deadline for testing.
- A prepared example course/offering, approved resource, practical task and role accounts.
- Required institutional permission, recruitment and consent arrangements before inviting participants. Participant numbers and composition remain to be approved; no sampling formula or invented population figure is used.
- A restricted evidence folder, pseudonymous participant codes, and a rule excluding passwords, tokens, academic IDs and real marks from recordings or reports.
- A designated facilitator, observer and defect recorder. Participation must not affect assessment; participants may stop a walkthrough.

## Role-based acceptance cases

Record each case as **Not run**, **Pass**, **Fail** or **Blocked**. Do not pre-fill the expected outcome as the observed result.

| Case | Role and steps | Expected outcome | Evidence to retain |
| --- | --- | --- | --- |
| UAT-01 | Register as Student/Lecturer; attempt sign-in before approval. | Pending account has no dashboard access; public Administrator registration is unavailable. | Status screen, account record and permission result. |
| UAT-02 | Administrator reviews registration, completes the approved academic-setup flow and allocates a course. | Correct role/hierarchy/access; account becomes active only through the authorised flow. | Before/after states and related audit event. |
| UAT-03 | Lecturer drafts, edits and publishes an assigned task; another Lecturer attempts to edit it. | Correct enrolled audience sees the published task; unauthorised edit fails. | Task record, publication notification and rejected request. |
| UAT-04 | Student opens an assigned task and records resource/version, parameters, session identifier, timing and outputs. | The draft preserves the intended educational work trail after reopening. | Draft record and relevant screenshots without private identity data. |
| UAT-05 | Upload permitted evidence; attempt unsupported/oversized evidence; confirm submission. | Valid evidence is protected; invalid evidence is rejected; confirmed attempt is read-only. | Validation messages, protected reference and confirmation timestamp. |
| UAT-06 | Lecturer requests correction; Student starts and submits the permitted resubmission. | Feedback is visible, attempts remain linked and the configured attempt limit is enforced. | Attempt history, feedback and notifications. |
| UAT-07 | Lecturer saves a grade without release; Student attempts access; Lecturer releases it. | Unreleased result remains private; released grade/feedback becomes available to its Student. | Assessment states, visibility checks and release notification. |
| UAT-08 | Student and Lecturer attempt another Student's evidence/result URL. | Access follows ownership and current teaching permission, not knowledge of an identifier. | Authorised/rejected response status, without retaining another person's file contents. |
| UAT-09 | Administrator issues a temporary password; account holder signs in and replaces it. | Temporary password appears once; forced change is enforced; no password enters the audit record. | Reset/change audit events and state checks; never record the password itself. |
| UAT-10 | Administrator filters/exports records; Lecturer/Student attempts Administrator reporting access. | Filter/export behaviour is correct; restricted reports remain Administrator-only. | Sanitised export and permission check. |
| UAT-11 | Launch the approved signed-return resource; exercise a valid callback and invalid, replayed, expired and late callbacks. | Only a valid bound return updates an editable draft; formal submission still requires Student confirmation. | Resource/version, opaque session reference, response status and audit event; redact tokens/signatures. |
| UAT-12 | Repeat main tasks at desktop/mobile widths and by keyboard; verify inactivity timeout. | No page-level overflow; visible focus and usable table scrolling; approximately five minutes of inactivity ends access. | Device/browser, screenshots, keyboard notes and timeout event. |
| UAT-13 | Capture a matched staging backup; restore into separate empty database/media volumes. | Record counts and protected evidence agree; recovery probes pass. | Backup manifest/checksums, restore log, reference counts and protected-download checks. |
| UAT-14 | Administrator edits an unused resource, disables/restores it, and revises a resource with history. | Edits/restoration require fresh approval; disabling blocks use without deleting records; historical metadata cannot be overwritten; revisions do not alter existing task links. | Resource states, retained task/evidence references and audit events. |
| UAT-15 | Administrator drafts/previews/sends a role or individual notice, retries sending, and cancels another draft. | No draft deliveries; only currently active eligible accounts receive notices; retry does not duplicate; cancelled/sent history is retained. | Audience preview, delivery/open counts and audit events. |
| UAT-16 | Eligible account is suspended and reactivated; an old browser attempts access afterwards. | Confirmation/reason required; old sessions remain invalid after reactivation; records remain; fresh authorised sign-in succeeds. | State/session checks and audit events, without passwords. |
| UAT-17 | Account holder requests support; another account attempts access; Administrator responds/resolves; support settings are updated. | Requests/responses are private to owners and Administrators; owner receives an update; public Help shows escaped contact/guidance only. | Permission checks, response/status, notification and audit events. |

UAT-09, UAT-13, UAT-14 and UAT-16 can disrupt access or records: use designated test accounts/resources and isolated staging/recovery targets. UAT-15 must use a synthetic audience, not real accounts without notice-delivery approval.

## Observation sheet

Use one entry per participant/task:

```text
Participant code: [not a name or academic identifier]
Role: [Administrator / Lecturer / Student]
Case ID:
Build/revision and environment:
Device/browser/version and viewport:
Task start time:
Task end time:
Outcome: [completed independently / completed with help / not completed]
Number and description of errors:
Assistance given:
Unexpected behaviour or unclear wording:
Evidence reference:
Observer and date:
```

Start task timing after the participant understands the instruction; stop when the required outcome is achieved or the attempt ends. Record pauses/help separately. Describe completion and error rules before the session. Do not convert CI/pytest runtime into these observations.

## Short feedback instrument

This is a project-specific exploratory questionnaire, **not a validated standard usability scale**. Use 1 = strongly disagree, 2 = disagree, 3 = neither agree nor disagree, 4 = agree, 5 = strongly agree, plus **Not applicable**.

1. I could find the tasks or records relevant to my role.
2. The instructions and next steps were clear.
3. I could tell whether work was a draft, submitted, returned or assessed.
4. I could understand what evidence was required and whether it had been saved.
5. The feedback/result screens were understandable where relevant to my role.
6. The distinction between approved demonstrations and physical workshop work was clear.
7. The interface was usable on the device used in the walkthrough.
8. Overall, the platform supported the management task I was asked to complete.

Open questions: What was most useful? What was confusing? What should be changed before regular use? Did the resource/instructions leave an important practical concept unclear?

Report the number of valid responses and response distributions per item. Keep **Not applicable** separate and disclose missing responses. Do not describe these items as a standard usability score or infer causal learning improvement from them.

## Performance and accessibility evidence

Performance checks remain planned. On a fixed staging build, record hardware/container resources, database engine/version, dataset size, network conditions, scenario, concurrency, warm-up and repeated requests. Measure server/request latency separately from browser rendering and resource-launch timing. Agree thresholds with the supervisor/deployment owner before accepting or rejecting measured results; this pack supplies no invented target or response time.

The developer axe matrix covers 25 page/role combinations at 1280 and 390 pixels. Retain its JSON/screenshots and review incomplete results manually, including colour contrast. Form description references are also checked directly. Add keyboard, screen-reader, zoom and representative browser/device checks. Zero automated violations is not full accessibility certification.

## Requirement gaps to resolve before sign-off

The source implementation should be compared against the approved prototype/brief rather than using green tests as the complete requirements list. Current visible gaps include:

- Special ID is captured in academic setup, not public registration.
- ATU logo, orange prototype navigation, greetings/rotating educational welcome/backgrounds need a fidelity review; the current backend interface uses a navy/blue theme.
- Permitted profile editing/photo upload is not implemented.
- Account recovery is Administrator-issued temporary passwords; self-service email forgot-password support is not implemented.
- Suitable Lecturer assessment-record export is not yet implemented; current exports are Administrator-only.
- General Help, private platform support, Administrator notice management, support settings and resource edit/disable/restore/revision controls are now implemented. Their proposed acceptance scenarios are UAT-14–17, not recorded participant findings. Deployment/security settings deliberately remain outside the database-editable interface; any additional settings require scope review.
- Demonstration parameter values are recorded as summaries, not schema-driven platform-enforced ranges; approved resources must define/enforce their limits, and the workflow needs academic review.
- Version/parameter changes during an open run need an agreed snapshot/freeze policy. A formal submission currently records the selected resource's version label; full immutable launch-version and parameter provenance must be checked before claiming complete run traceability.
- Actual-resource staging integration, operational abuse throttling/monitoring, PostgreSQL/container startup, recovery rehearsal and manual accessibility remain unverified release gates.

Do not silently waive these requirements. Record each as implement-before-release, accepted limitation with approval, or deferred with a named owner. No public “View As” feature is to be introduced.

## Defect and retest record

```text
Defect ID / linked UAT case or objective:
Observed build/environment:
Severity: [critical / major / minor]
Reproduction steps:
Expected / actual behaviour:
Sanitised evidence reference:
Owner / proposed correction:
Corrected build:
Retest steps and observed outcome:
Reviewer / date / closure decision:
```

Permission bypass, private-data leakage or confirmed-record corruption is critical. A blocked principal role workflow is major. Cosmetic/wording problems without workflow impact are minor, unless accessibility effects make them more serious. This is a proposed project classification, not an institutional policy claim.

## Sign-off and Chapter Four handoff

Keep the initial status **Not ready for institutional release** until the recorded release gates and agreed requirements are closed. Sign-off requires the reviewed build, observed outcomes, unresolved limitations and responsible reviewers—not just a percentage of green tests.

Chapter Four can later present: implemented role workflows; actual environment/configuration; reproducible developer-test evidence; deployment and recovery observations; real usability results; correction/retest history; objective-by-objective findings; and limitations. Leave participant counts, questionnaire distributions, timings, performance measurements and learning-effect claims blank until genuine data exists.
