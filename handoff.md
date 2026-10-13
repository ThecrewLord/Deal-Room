# Deal Room V2 — Frontend Handoff / Implementation Contract

## Purpose

This document is the frontend handoff for the **implemented Deal Room V2 backend**.

Use this document as the implementation guide for the frontend running against the current V2 backend.

The backend changes in the supplied implementation reports have already been implemented across Groups 1, 2, and 4–10. The frontend must now align its UI, API calls, validation, role-based visibility, workflow actions, and local database/migration state with those backend changes.

**Important:** The backend is authoritative. The frontend must not recreate business rules that belong to the backend or trust client-controlled workflow fields.

---

# 1. V2 Backend Architecture You Must Target

The authoritative backend components are:

- `LifecycleTransitionService` — lifecycle transitions
- `AuthorizationService` — authorization
- `OpportunityTeam` — Solution Engineer assignment relationship
- `Phase2Service` — POC/Phase 2 workflow
- `POCTracker` — current POC state
- `POCTeamMember` — POC team membership
- `POCHistory` — immutable POC business history
- `ClosedWonRequest` — generic closure-request persistence for both Closed Won and Closed Lost
- `NotificationService` — notifications
- `ActivityService` / `AuditLog` — audit/activity architecture
- `DeliveryProject` / `DeliveryProjectMember` — Delivery aggregate

Do **not** introduce another lifecycle engine, POC model, assignment table, closure engine, notification system, or Delivery Project model.

---

# 2. Canonical Lifecycle

The backend lifecycle is:

```text
Lead
  ↓
Qualified
  ↓
RFX
  ↓
POC
  ↓
Negotiations
  ↓
Delivery
```

Outcomes are separate:

```text
Open
Closed Won
Closed Lost
```

Operational status is separate:

```text
Active
Stalled
Closed
```

### Frontend rules

Do not implement:

```text
Closed Won = lifecycle stage
Closed Lost = lifecycle stage
```

They are outcomes.

Do not allow the frontend to send arbitrary:

```text
lifecycle_stage
outcome
operational_status
review_status
deal_finder_id
```

through ordinary opportunity update requests.

The backend explicitly rejects client-controlled workflow mutation.

---

# 3. Technical Workflow Ownership

After the opportunity reaches `Qualified`:

```text
Pre-Sales Manager
       ↓
Assign Solution Engineer
       ↓
Solution Engineer
       ↓
RFX
       ↓
POC (if required)
       ↓
Negotiations
```

The assigned Solution Engineer owns technical progression.

### Qualified → RFX

Only the **assigned Solution Engineer** should be shown the action to enter RFX.

Sales Executive must not receive a technical stage-transition action.

An unassigned Solution Engineer must not receive the action.

PSM role alone does not give technical transition authority.

### RFX → POC

The assigned Solution Engineer can initiate RFX → POC when the backend requirements are satisfied.

The backend requires authoritative RFX Drive context.

Do not attempt to verify Google Drive permissions from the frontend.

### POC → Negotiations

This is an explicit Solution Engineer action.

Do **not** automatically move an opportunity to Negotiations because:

- a POC was submitted;
- a result link exists;
- a POC succeeded.

The user-facing UI should provide an explicit action for the assigned SE.

---

# 4. Pre-Sales Manager → Solution Engineer Assignment

The authoritative relationship is:

```text
Opportunity
   ↓
OpportunityTeam
   ↓
User
   +
Solution Engineer role
```

No separate `solution_engineer_assignments` table/model exists.

### Assignment UI

The assignment screen/action should:

1. Be available only to an authorized Pre-Sales Manager.
2. Load valid Solution Engineer candidates.
3. Submit the selected user and current `row_version`.
4. Handle `409` concurrency errors.
5. Refresh the opportunity/team state after success.

Do not send:

- lifecycle stage
- outcome
- operational status
- Deal Finder
- arbitrary team roles

as part of the assignment action.

### Candidate requirements

The backend validates that the candidate:

- exists;
- is active;
- actually has the Solution Engineer role;
- is eligible.

The frontend may provide client-side filtering for UX, but the backend remains authoritative.

### Assignment state

Assignment is allowed only in the required `Qualified` / open / active state.

Do not show the assignment action for:

- Lead
- RFX
- POC
- Negotiations
- Delivery
- Closed Won
- Closed Lost

The backend rejects these states.

---

# 5. RFX Changes

RFX is now a lightweight external-document reference.

The RFX Drive folder is the source of truth for documents such as:

- RFP
- RFQ
- POC Agreement
- client documents
- POC objective
- success criteria
- exit criteria
- technical requirements

The Deal Room should store the Drive folder reference rather than duplicating those documents/content.

### Frontend must NOT build fields for:

- RFP content
- RFQ content
- POC agreement content
- technical document content
- POC objective
- success criteria
- exit criteria

Those belong in the external Drive workspace.

### Drive permissions

Do not display language such as:

> Google Drive permissions verified

The backend does not verify Drive permissions.

Use neutral wording such as:

> Drive folder reference

or

> Open external Drive folder

### RFX → POC

The RFX Drive context is required for the RFX → POC transition.

If the backend rejects the transition because RFX context is missing, display the backend error rather than attempting to bypass it.

---

# 6. POC Model Changes

## Authoritative model

The authoritative current POC model is:

```text
POCTracker
    +
POCTeamMember
```

There is no second legacy `poc` model/table that the frontend should target.

The existing `/api/poc` routes are compatibility facades and delegate to the authoritative Phase2Service. They should not be treated as a separate POC architecture.

---

## Removed POC fields

The following fields were removed from the authoritative POC model:

```text
objective
success_metric
exit_criteria
failure_condition
input_drive_link
```

Do not send these fields to the backend.

Do not render them as Deal Room-owned POC form fields.

Do not keep frontend state assuming these fields exist in the V2 POC response.

The Group 4 implementation explicitly rejects obsolete document/content fields.

---

## Current POC request fields

The implemented `request_poc()` flow accepts the retained workflow fields:

```text
poc_name
target_date
remarks
```

Use the actual backend response/schema as the final API contract.

Do not reintroduce the removed POC document fields.

---

# 7. POC History

The backend now has an immutable:

```text
poc_history
```

table.

Fields:

```text
history_id
opportunity_id
actor_id
event_type
reason
created_at
```

Supported events:

```text
POC_STARTED
POC_SUBMITTED
NEW_POC_REQUESTED
```

History is append-only.

Previous POC history must not be edited or deleted from the frontend.

There is intentionally no public history mutation endpoint.

If a history display is later exposed through an API, treat it as read-only.

---

# 8. First POC Workflow

First POC flow:

```text
Solution Engineer
      ↓
Request POC
      ↓
Delivery Manager
      ↓
Assign DevOps Engineer / Data Analyst
      ↓
POC execution
      ↓
Submit result link
      ↓
Solution Engineer notified
```

The first POC can have a maximum of:

```text
2 members
```

Allowed POC team roles:

```text
DevOps Engineer
Data Analyst
```

Do not add generic Delivery Employee as a POC role.

---

# 9. Repeat POC Workflow

Repeat POC is now an explicit backend action.

Endpoint:

```http
POST /api/v2/opportunity/<opportunity_id>/pocs/request-new
```

Request:

```json
{
  "reason": "Customer requested another validation cycle",
  "row_version": 1
}
```

### Frontend behavior

Show the action to the authorized assigned Solution Engineer when:

- opportunity is visible;
- opportunity is open;
- lifecycle stage is `POC`;
- an existing submitted/completed POC exists;
- an existing POC team exists.

The reason is required.

Do not allow the frontend to provide:

```text
actor_id
user_id
role
event_type
created_at
assignment/member fields
```

The backend derives actor identity from authentication.

### Successful repeat POC

The backend:

1. preserves previous POC data;
2. creates a new POC cycle;
3. reuses the existing DE/DA team;
4. creates `NEW_POC_REQUESTED` history;
5. records activity;
6. notifies the existing POC team;
7. remains in lifecycle stage `POC`.

### Critical UI rule

**Do not involve the Delivery Manager in repeat POC requests.**

The Delivery Manager is involved in the first POC team assignment, not repeat POCs.

### Recipient behavior

Repeat POC notification goes to the existing:

- DevOps Engineer
- Data Analyst

team members.

The Delivery Manager is not a repeat-POC recipient.

---

# 10. POC Submission

Canonical endpoint retained:

```http
POST /api/v2/pocs/<poc_id>/submit
```

Request body:

```json
{
  "result_view_link": "https://example.com/result",
  "row_version": 7
}
```

Only these submission fields should be sent.

Do NOT send:

```text
status
submitted_by
submitted_at
outcome
outcome_notes
```

The backend derives those values.

### Who can submit?

The actor must be:

- authenticated;
- active/approved;
- DevOps Engineer OR Data Analyst;
- an exact member of the POC team;
- operating on an open opportunity;
- operating while lifecycle stage is `POC`;
- operating while outcome is `Open`;
- operating while the POC is in an allowed active state.

### Result immutability

A submitted POC result cannot be overwritten by another normal submission.

The frontend should therefore treat:

```text
submitted_at != null
```

as an immutable submission state.

Do not display an ordinary "Edit submitted result" operation.

---

# 11. POC Submission Concurrency

POC submission requires the current:

```text
row_version
```

The backend performs an atomic optimistic-concurrency update.

A stale version returns the existing `409` conflict path.

### Frontend behavior

On `409`:

1. do not overwrite local state;
2. display a concurrency/conflict message;
3. refresh the POC;
4. let the user review the latest state.

Do not automatically retry with a new version without user/context awareness.

---

# 12. POC Submission Notification

After a successful POC submission:

```text
POC team member
      ↓
POC_SUBMITTED
      ↓
assigned Solution Engineer
```

The frontend should not ask the submitter to choose the notification recipient.

The backend resolves the assigned SE from `OpportunityTeam`.

---

# 13. No-POC Closure Workflow

An assigned Solution Engineer can request closure when the opportunity is:

```text
Qualified
OR
RFX
```

and no POC is required.

The workflow is:

```text
Solution Engineer
       ↓
Request Closure
       ↓
Pre-Sales Manager
       ↓
Approve / Reject
       ↓
Closed Won / Closed Lost
```

Endpoint:

```http
POST /api/opportunities/<id>/request-closure
```

The exact request schema should be taken from the current backend schema.

Conceptually:

```json
{
  "requested_outcome": "Closed Won",
  "row_version": 5
}
```

or:

```json
{
  "requested_outcome": "Closed Lost",
  "reason": "Client selected another provider.",
  "row_version": 5
}
```

---

# 14. Closed Lost Validation

For Closed Lost:

```text
reason = required
```

If:

```text
reason = Other
```

then:

```text
explanation = required
```

For other reasons, explanation is optional according to the existing closure rules.

Frontend validation can provide immediate feedback, but backend validation remains authoritative.

---

# 15. Closure Request Does NOT Immediately Close

When the SE submits a closure request:

```text
outcome remains Open
operational_status remains Active
lifecycle_stage remains unchanged
```

The request is an approval object.

The PSM must review it.

### PSM actions

The PSM can:

```text
Approve
Reject
```

A rejected request leaves the opportunity open at the same lifecycle stage.

Do not implement:

```text
SE clicks Request Closure
        ↓
Frontend immediately marks opportunity Closed
```

That is incorrect.

---

# 16. Generic Closure API

The current authoritative closure routes are:

```http
POST /api/opportunities/<id>/request-closure
POST /api/opportunities/<id>/approve-closure
POST /api/opportunities/<id>/reject-closure
```

The old Closed Won-only routes were removed in Group 9/10:

```text
request-closed-won
approve-closed-won
reject-closed-won
```

Do not call those routes.

Do not implement frontend fallbacks to those obsolete routes.

---

# 17. Closure Persistence

The backend retains:

```text
closed_won_requests
```

but it now represents the generic closure-request mechanism for both:

```text
Closed Won
Closed Lost
```

The database changes include:

- removal of the old one-request-per-opportunity unique constraint;
- `requested_outcome`;
- `requested_reason`;
- `requested_explanation`;
- a Closed Won / Closed Lost check constraint.

Multiple closure requests/history are therefore supported by the backend model.

The frontend should not assume there can only ever be one historical closure request.

---

# 18. Closed Won → Delivery

Every authorized Closed Won triggers the Delivery handoff behavior.

The existing Delivery architecture is reused:

```text
DeliveryProject
DeliveryProjectMember
```

No second Delivery Project model exists.

If the opportunity has a POC team:

```text
POC DE/DA members
       ↓
Suggested Delivery members
```

These are **suggestions only**.

The POC team is not silently finalized as the Delivery team.

The Delivery Manager can:

- approve the suggested team;
- change the team;
- choose a different team.

If there was no POC team:

```text
Delivery team starts without pre-selected members
```

---

# 19. Closed Won Notification

Every Closed Won must result in Delivery Manager notification.

This is true regardless of the stage from which the authorized Closed Won occurred.

The frontend should display the resulting Delivery handoff state/notification as returned by the backend.

Do not create a separate frontend-only notification path.

---

# 20. Deal Finder

Deal Finder remains immutable.

The user who created/founded the opportunity remains the Deal Finder.

The frontend must not provide an ordinary edit control for:

```text
Deal Finder
```

Group 10 also explicitly protects `deal_finder_id` from generic opportunity update mutation.

---

# 21. Generic Opportunity Update

The ordinary opportunity update API must not be used to modify:

```text
lifecycle_stage
outcome
operational_status
review_status
deal_finder_id
```

Workflow changes must use explicit backend actions.

This means the frontend should model actions such as:

```text
Approve Lead
Assign SE
Enter RFX
Request POC
Submit POC
Request New POC
Request Closure
Approve Closure
Reject Closure
Enter Negotiations
Close Won
Close Lost
```

as domain actions rather than one generic "Update Opportunity" operation.

---

# 22. Role-Based UI Expectations

The frontend should derive visible actions from backend authorization and current resource state.

Important examples:

### Sales Executive

Should not receive technical stage-transition controls after qualification.

Should not receive ordinary Closed Won authority.

### Solution Engineer

Can receive:

- Qualified → RFX
- RFX → POC
- POC → Negotiations
- repeat POC
- no-POC closure request

when the backend relationship/state requirements are satisfied.

### Pre-Sales Manager

Can receive:

- assign Solution Engineer
- closure approval/rejection where authorized

### Delivery Manager

Handles:

- first POC team assignment
- Delivery team assignment/change

Does NOT handle repeat POC requests.

### DevOps Engineer / Data Analyst

Can submit a POC result only when they are assigned to the POC team.

---

# 23. API Error Handling

The frontend must correctly handle backend authorization and validation responses.

Especially:

```text
403
```

for authorization failures.

```text
409
```

for optimistic-concurrency conflicts and relevant state conflicts.

For `409`:

```text
Do not overwrite current state.
Refresh the resource.
Show the user that the record changed.
Allow them to review the latest state.
```

Do not silently retry mutations with a newer version.

---

# 24. Local Database / Migration Changes

If your frontend environment uses the same local backend PostgreSQL database, the database must be brought to the current Alembic head.

### Current authoritative migration head

The Group 10 migration graph was repaired to one head:

```text
a1c2d3e4f5g6
```

Migration:

```text
migrations/versions/a1c2d3e4f5g6_merge_group8_with_main.py
```

It is a no-op Alembic merge migration whose purpose is to join the previously branched Group 8 migration with the main migration chain.

### Important

Do NOT manually edit the PostgreSQL schema.

Do NOT modify the baseline migration:

```text
60ba9620bb40_deal_room_v2_baseline.py
```

Do NOT restore the legacy migration chain.

Do NOT use files under:

```text
migrations/versions_legacy/
```

as the active migration chain.

---

# 25. Database Schema Changes Introduced by V2 Groups

## POC document-field removal

Migration:

```text
8a4b6c7d9e01
```

The following columns were removed from `poc_tracker`:

```text
objective
success_metric
exit_criteria
failure_condition
input_drive_link
```

Do not recreate them in the frontend database.

---

## POC history

Migration:

```text
9b5c7d1e2f34
```

Adds:

```text
poc_history
```

with:

```text
history_id
opportunity_id
actor_id
event_type
reason
created_at
```

History is immutable.

---

## Closure workflow

Migration:

```text
7f8e9d0c1b2a_group8_closure_workflow.py
```

Changes:

```text
closed_won_requests
```

by:

- removing the one-request-per-opportunity unique constraint;
- adding `requested_outcome`;
- adding `requested_reason`;
- adding `requested_explanation`;
- adding a Closed Won / Closed Lost constraint.

---

## Migration graph merge

Migration:

```text
a1c2d3e4f5g6_merge_group8_with_main.py
```

does not change application tables.

It merges the two Alembic branches into one head.

---

# 26. Expected Migration Chain

The reports establish the V2 chain as including:

```text
60ba9620bb40
        ↓
7f8e9d0c1b2a
        ↓
8a4b6c7d9e01
        ↓
9b5c7d1e2f34
        ↓
a1c2d3e4f5g6
```

The supplied Group 4 report references an earlier RFX migration as its down revision, while the separate Group 3 implementation report was **not included in the supplied ZIP of reports**. Therefore, do not manually reconstruct missing Group 3 migration history.

Use the actual backend migration graph:

```bash
flask db heads
flask db current
```

The expected final head is:

```text
a1c2d3e4f5g6
```

---

# 27. Recommended Local Database Procedure

From the backend environment:

```bash
cd backend
```

Activate the project's existing virtual environment.

Then:

```bash
flask db heads
```

Expected:

```text
a1c2d3e4f5g6
```

Then:

```bash
flask db current
```

Your local database should eventually report:

```text
a1c2d3e4f5g6
```

Then:

```bash
flask db check
```

Expected:

```text
No new upgrade operations detected.
```

Then:

```bash
flask db upgrade
```

If you are intentionally creating a fresh V2 local database, use the project's normal database reset/bootstrap process rather than manually recreating tables.

After migration:

```bash
flask db current
```

must resolve to:

```text
a1c2d3e4f5g6
```

---

# 28. Do Not Use the Obsolete Seed Dataset

The old seed/demo data is obsolete.

Do not make frontend development dependent on:

```text
seed_v2.py
seed_data.py
seed_test_data.py
app/seed/seed_opportunities.py
app/seed/seed_phase2.py
app/seed/seed_poc.py
app/seed/seed_accounts.py
app/seed/seed_users.py
app/seed/seed_stakeholders.py
app/seed/seed_oem.py
app/seed/run_seed.py
app/seed/reset_v2_demo.py
app/seed/seed_admin.py
```

The backend cleanup removed the stale root:

```text
seed_v2.py
```

and cleaned stale seed references.

A new business/demo dataset will be created separately.

Do not treat old seed records as proof of correct V2 behavior.

---

# 29. Frontend Fields That Must Be Removed

Remove old POC form/detail state for:

```text
objective
success_metrics / success_metric
exit_criteria
failure_condition
input_drive_link
```

Also remove any UI that implies Deal Room stores those documents/content.

Do not simply hide the fields while continuing to send them.

Remove them from:

- TypeScript interfaces/types
- API request DTOs
- API response types
- form validation
- form submission payloads
- Redux/Zustand/store state
- detail cards
- edit dialogs
- filters/search
- PDF/report UI
- test fixtures
- mock API responses

---

# 30. New Frontend UI/UX Areas Required

Implement/update UI for:

### Opportunity

- Deal Finder displayed as immutable.
- lifecycle stage displayed separately from outcome.
- operational status displayed separately.
- role/state-specific action controls.

### Assignment

- PSM → Solution Engineer assignment.

### RFX

- Drive folder reference.
- External-document workspace link.
- No document-content duplication.

### POC

- current POC state;
- POC team;
- result view link;
- submission state;
- repeat POC action;
- repeat POC reason;
- immutable history display when supported by the API.

### Closure

- request closure;
- requested outcome;
- Closed Lost reason;
- Closed Lost explanation when reason is `Other`;
- PSM approval;
- PSM rejection;
- pending/approved/rejected state.

### Delivery

- Delivery Manager notification state;
- suggested POC-derived Delivery members;
- final Delivery team remains editable by Delivery Manager.

---

# 31. Do Not Recreate These Backend Rules in the Frontend

The frontend may provide UX validation, but it must never become the security boundary.

Do not rely on frontend logic to enforce:

- role authorization;
- Solution Engineer assignment;
- stage transitions;
- opportunity ownership;
- outcome changes;
- closure authority;
- POC team membership;
- row versions;
- IDOR protection;
- Deal Finder immutability;
- closed-record locking.

The backend derives authoritative values from authenticated context and persisted relationships.

---

# 32. Optimistic Concurrency

The frontend must preserve `row_version` wherever the backend action requires it.

Typical mutation pattern:

```text
GET resource
   ↓
read row_version
   ↓
perform domain action with row_version
   ↓
success → replace local resource with server response
```

If `409`:

```text
mutation rejected
      ↓
refresh resource
      ↓
show conflict
      ↓
user reviews current state
```

Do not silently use a newer version to repeat a mutation.

---

# 33. Notifications

Continue using the backend notification system.

Important implemented events include:

```text
SOLUTION_ENGINEER_ASSIGNED
POC_REQUESTED
POC_SUBMITTED
NEW_POC_REQUESTED
CLOSURE_APPROVAL_REQUESTED
CLOSURE_APPROVED
CLOSURE_REJECTED
CLOSED_WON
CLOSED_LOST
DELIVERY_PROJECT_CREATED
```

Use the actual backend notification response/type names when integrating.

Do not create a second frontend-only notification model that attempts to replace backend notifications.

---

# 34. Legacy APIs That Must Not Be Used

Do not call:

```http
POST /api/opportunities/<id>/request-closed-won
POST /api/opportunities/<id>/approve-closed-won
POST /api/opportunities/<id>/reject-closed-won
```

These were removed by Groups 9/10.

Use:

```http
POST /api/opportunities/<id>/request-closure
POST /api/opportunities/<id>/approve-closure
POST /api/opportunities/<id>/reject-closure
```

---

# 35. Compatibility `/api/poc` Routes

The backend still retains these compatibility routes:

```http
POST /api/poc/request
GET  /api/poc/eligible-opportunities
GET  /api/poc/<id>
GET  /api/poc/opportunity/<id>
POST /api/poc/<id>/complete
GET  /api/poc/<id>/download
```

These are **thin compatibility facades** over the authoritative `Phase2Service`.

They are not a second POC implementation.

For new frontend work, prefer the current V2 API surface where an equivalent V2 route exists.

Do not build new business logic around the assumption that `/api/poc` is a separate domain.

---

# 36. Testing Requirements for Frontend

At minimum test:

## Lifecycle

- Sales Executive cannot perform technical transitions.
- Unassigned SE cannot enter RFX.
- Assigned SE can enter RFX.
- RFX → POC requires RFX context.
- POC → Negotiations is explicit.
- POC submission does not automatically move to Negotiations.
- Stage skipping is not exposed as valid UI actions.

## Assignment

- PSM can assign valid SE.
- Other roles do not see/use the action.
- Invalid candidate produces backend error.
- Closed opportunity cannot be assigned.

## POC

- First POC team assignment.
- Maximum two members.
- Only DE/DA roles.
- POC submission.
- Submitted result cannot be edited normally.
- Repeat POC requires reason.
- Repeat POC does not involve DM.
- Existing DE/DA are the repeat-PPOC recipients.

## Closure

- SE can request closure from Qualified/RFX when authorized.
- Request does not immediately close opportunity.
- PSM can approve.
- PSM can reject.
- Closed Lost validation works.
- Closed Won/Lost are displayed as outcomes.
- Old Closed Won-only routes are not called.

## Concurrency

Test `409` handling for:

- assignment;
- repeat POC;
- POC submission;
- closure request/approval.

---

# 37. Backend Verification Before Integration

The implementation reports show that several groups were source/compile verified but could not execute their full runtime suites because the implementation environment lacked Flask dependencies.

Therefore, after connecting the frontend to the backend, run the backend verification in the project's normal `.venv`:

```bash
cd backend

python -m compileall app tests migrations

pytest

flask db check
flask db heads
flask db current
```

For a clean database:

```bash
flask db upgrade
```

Expected final migration head:

```text
a1c2d3e4f5g6
```

Do not report the complete V2 integration as verified solely because `compileall` succeeds.

---

# 38. Important Known Verification Status

The supplied reports contain these verification limitations:

### Group 1

Latest reported full suite:

```text
95 passed
1 failed
1 skipped
97 total
```

The failure was:

```text
tests/test_opportunity_lifecycle.py::test_group1_stage_skipping_rejected[POC-Delivery]
```

The transition was correctly rejected, but the implementation raised `AuthorizationDenied` while the test expected `TransitionInvalid`.

### Group 2

Group 2-specific tests passed in the reported run.

The same overall suite was:

```text
95 passed
1 failed
1 skipped
```

### Groups 4, 5, 6, 7, 8, 10

The implementation environments reported compile/static verification, but full runtime pytest/Alembic execution was blocked because Flask and related dependencies were unavailable.

Therefore, do not describe the entire backend as fully runtime-certified solely from these implementation reports.

---

# 39. Final Frontend Definition of Done

The frontend implementation is complete when:

- [ ] frontend uses the canonical V2 lifecycle;
- [ ] lifecycle, outcome, and operational status are separate;
- [ ] generic opportunity update cannot mutate workflow state;
- [ ] PSM → SE assignment UI is implemented;
- [ ] only valid SE candidates can be selected;
- [ ] RFX uses a Drive reference rather than duplicated document fields;
- [ ] obsolete POC fields are removed from frontend models/forms;
- [ ] first POC team workflow is supported;
- [ ] POC result submission uses `result_view_link + row_version`;
- [ ] repeat POC uses `reason + row_version`;
- [ ] repeat POC does not involve Delivery Manager;
- [ ] POC history is treated as immutable;
- [ ] no-POC closure request is supported;
- [ ] PSM approval/rejection is supported;
- [ ] Closed Lost reason/explanation validation is supported;
- [ ] obsolete Closed Won-only APIs are no longer called;
- [ ] Closed Won → Delivery state is displayed correctly;
- [ ] suggested Delivery members are clearly presented as suggestions;
- [ ] `409` concurrency conflicts are handled safely;
- [ ] role-based action visibility is implemented;
- [ ] frontend does not rely on UI authorization for security;
- [ ] local database is migrated to `a1c2d3e4f5g6`;
- [ ] obsolete POC columns are not recreated;
- [ ] old seed data is not treated as authoritative;
- [ ] frontend build passes;
- [ ] backend/API integration tests pass in the real project environment.

---

# 40. Quick Start for the Frontend Teammate

Start by checking the backend migration state:

```bash
cd backend

flask db heads
flask db current
flask db check
```

Expected final head:

```text
a1c2d3e4f5g6
```

Then inspect the current API schemas/routes rather than relying on old frontend types.

Priority order for frontend implementation:

```text
1. Remove obsolete POC fields
2. Update lifecycle/action model
3. Implement PSM → SE assignment
4. Update RFX UI
5. Update first POC UI
6. Implement POC submission contract
7. Implement repeat POC
8. Implement closure request/approval
9. Update Delivery handoff UI
10. Remove calls to obsolete Closed Won APIs
11. Update role-based action visibility
12. Handle row_version / 409 conflicts
13. Run frontend build + integration tests
```

## Core principle

**The backend is the source of truth for authorization, workflow state, ownership, concurrency, and business rules.**

The frontend should present the actions the user is allowed to perform, submit explicit domain actions, display backend state, and gracefully handle backend rejection/conflicts. It must not become a second workflow engine.
