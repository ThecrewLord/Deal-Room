# Deal Room V2 --- Backend Change Specification

## 1. Objective

Modify the existing backend to implement the revised workflow without
creating a second workflow engine.

First audit the existing implementation.

Classify existing code as:

``` text
KEEP
MODIFY
REPLACE
DELETE
NEW
```

Do not preserve redundant legacy behavior.

------------------------------------------------------------------------

# 2. Lifecycle and Transition Engine

## KEEP

The existing centralized lifecycle transition mechanism.

Do not create another state machine.

The canonical lifecycle remains:

``` text
Lead → Qualified → RFX → POC → Negotiations → Delivery
```

## MODIFY

Stage authorization must reflect the revised ownership:

``` text
Qualified → RFX
    Solution Engineer

RFX → POC
    Solution Engineer

POC → Negotiations
    Solution Engineer

Negotiations → Delivery
    Existing final approval rules
```

Do not allow Sales Executive to perform technical stage transitions.

------------------------------------------------------------------------

# 3. Pre-Sales Manager → Solution Engineer Assignment

The existing technical assignment system should be reused if it is still
the authoritative `OpportunityTeam` mechanism.

Required workflow:

``` text
Sales Manager
    ↓
Approve + assign Sales Executive
    ↓
Opportunity becomes Qualified
    ↓
Pre-Sales Manager receives assignment work
    ↓
Pre-Sales Manager assigns Solution Engineer
    ↓
SE becomes authorized technical participant
```

Backend must verify that the selected user actually has the Solution
Engineer role.

Do not trust the frontend.

If an assignment already exists, do not create a duplicate assignment
model.

------------------------------------------------------------------------

# 4. Solution Engineer Technical Authority

The authorization layer must evaluate:

-   authenticated user
-   active role
-   opportunity visibility
-   assigned Solution Engineer relationship
-   current lifecycle stage
-   outcome
-   operational status
-   requested action
-   row_version

The SE must be able to:

### Qualified → RFX

Only if:

-   opportunity is open
-   actor is assigned SE
-   correct active role
-   concurrency token is valid

### RFX → POC

Only if:

-   opportunity is open
-   actor is assigned SE
-   POC is required
-   RFX Drive context exists
-   concurrency token is valid

------------------------------------------------------------------------

# 5. RFX Context

## MODIFY

Current RFX implementation must be reduced to a lightweight Drive
reference.

The required persisted information should be approximately:

``` text
opportunity_id
drive_folder_link
created_by
created_at
updated_by
updated_at
row_version
```

Do not add:

``` text
rfp_content
rfq_content
poc_agreement_content
success_metrics
exit_criteria
technical_document_content
```

Those live in Drive.

## Important

The current Phase 2 documentation previously described the Drive link as
mandatory at RFX → POC.

That remains appropriate, but the content itself is external.

The application must not verify Drive permissions.

------------------------------------------------------------------------

# 6. POC Architecture

## IMPORTANT

The project history contains references to two old POC structures:

``` text
poc
poc_tracker
```

The implementation must have ONE authoritative V2 POC model.

Inspect the actual current repository and determine which model is
authoritative.

If `poc_tracker` is the current authoritative implementation, keep it
and remove the old competing `poc` implementation.

Do not maintain both.

------------------------------------------------------------------------

# 7. Remove Redundant POC Requirement Fields

The new workflow intentionally removes these from the Deal Room POC
form/detail model:

``` text
objective
success_metrics
exit_criteria
POC agreement document
technical requirements
RFP/RFQ document fields
```

These are maintained in the RFX Drive folder.

Before removing fields from the database:

-   inspect all backend references
-   inspect seed data
-   inspect serializers
-   inspect frontend API consumers
-   inspect tests
-   inspect reporting/dashboard queries

Do not leave dead fields simply because they already exist.

If they are no longer part of the domain contract, create a migration to
remove them after all callers are removed.

If a field is still required for compatibility during a staged
migration, explicitly mark it as deprecated and schedule removal.

------------------------------------------------------------------------

# 8. POC Current State

The authoritative POC record should focus on:

``` text
opportunity_id
status
assigned POC members
current/result view link
submitted_by
submitted_at
timestamps
row_version
```

Plus the relationship to lightweight history.

Do not create a separate database record for every demo artifact unless
inspection proves it is necessary for the existing integrity model.

------------------------------------------------------------------------

# 9. POC History

Add a lightweight immutable history mechanism if the current system does
not already provide one.

Recommended structure:

``` text
poc_history
------------
history_id
opportunity_id
actor_id
event_type
reason
created_at
```

Possible event types:

``` text
POC_STARTED
POC_SUBMITTED
NEW_POC_REQUESTED
```

The important requirement is:

``` text
NEW_POC_REQUESTED
+
reason
+
actor
+
timestamp
```

Previous history must never be overwritten.

------------------------------------------------------------------------

# 10. Request New POC

Create an explicit domain action.

Conceptually:

``` text
POST /api/poc/<opportunity_id>/request-new
```

Use the project's existing API naming conventions rather than blindly
adopting this exact path.

Request:

``` json
{
  "reason": "Client requested additional API integration.",
  "row_version": 7
}
```

Backend must:

1.  Authenticate.
2.  Verify active role = Solution Engineer.
3.  Verify actor is assigned to the opportunity.
4.  Verify opportunity is open.
5.  Verify opportunity is in POC.
6.  Validate non-empty reason.
7.  Persist immutable POC history.
8.  Create notification event for existing POC team.
9.  Use optimistic concurrency.
10. Commit atomically.
11. Publish notification after successful commit.

The action must NOT:

-   involve Delivery Manager
-   overwrite previous submitted data
-   erase previous history
-   create duplicate assignments
-   move the opportunity to another lifecycle stage

------------------------------------------------------------------------

# 11. Repeat POC Notification

After `NEW_POC_REQUESTED`:

``` text
Solution Engineer
       ↓
existing POC team
       ↓
DevOps Engineer / Data Analyst
```

The Delivery Manager is not a recipient.

Reuse the existing NotificationService.

Do not introduce another notification implementation.

------------------------------------------------------------------------

# 12. POC Submission

The POC execution team:

``` text
DevOps Engineer
Data Analyst
```

can submit a result/view link.

Required:

``` text
result_view_link
row_version
```

The backend validates:

-   actor is an assigned POC member
-   active role matches
-   opportunity is open
-   POC is active/requested/in-progress according to actual status model
-   link is syntactically valid enough for application requirements
-   concurrency is valid

After submission:

-   record submitter
-   record timestamp
-   audit
-   notify assigned Solution Engineer

Do not claim Drive permission verification.

------------------------------------------------------------------------

# 13. No-POC Closure Approval

Add an explicit closure-request action.

Conceptually:

``` text
POST /api/opportunities/<id>/request-closure
```

Request:

``` json
{
  "requested_outcome": "Closed Won",
  "row_version": 5
}
```

or:

``` json
{
  "requested_outcome": "Closed Lost",
  "reason": "Client selected another provider.",
  "row_version": 5
}
```

The actual endpoint should follow existing API conventions.

## Authorization

A Solution Engineer may request closure when:

``` text
lifecycle_stage IN (
    Qualified,
    RFX
)
AND outcome = Open
AND actor is assigned Solution Engineer
```

The request goes to:

``` text
Pre-Sales Manager
```

The SE does not directly close the opportunity through this action.

------------------------------------------------------------------------

# 14. PSM Closure Approval

The PSM receives the closure request.

The PSM can:

``` text
Approve Closed Won
Approve Closed Lost
```

For Closed Lost:

-   reason required
-   if reason = Other, explanation required according to existing frozen
    closure rules

On approval:

``` text
outcome = Closed Won / Closed Lost
operational_status = Closed
```

Opportunity becomes locked.

Audit and notification must be generated.

Use the existing closure service if one exists.

Do not create a second closure engine.

------------------------------------------------------------------------

# 15. Closed Won / Closed Lost At Any Stage

The backend must support authorized closure at:

``` text
Lead
Qualified
RFX
POC
Negotiations
```

and any other stage explicitly permitted by the frozen authorization
matrix.

Do not hard-code:

``` text
only Negotiations can Closed Won
```

The authorization policy decides whether the current actor can perform
the closure.

Closed outcomes remain terminal.

------------------------------------------------------------------------

# 16. Closed Won → Delivery Notification

Every Closed Won must trigger a Delivery Manager notification.

This applies regardless of the lifecycle stage where Closed Won
occurred.

Use the existing domain-event/notification architecture.

Do not create a second delivery notification path.

------------------------------------------------------------------------

# 17. Delivery Team Preselection

When Closed Won occurs:

``` text
Did this opportunity have a POC team?
```

If yes:

``` text
POC DE/DA members
    ↓
suggested/pre-selected Delivery members
```

If no:

``` text
no pre-selected members
```

The Delivery Manager then:

``` text
Approve
OR
Change team
```

The POC team must not be silently finalized as the Delivery team.

------------------------------------------------------------------------

# 18. Delivery Project Creation

Use the existing DeliveryProject aggregate.

Do not create another project model.

The Delivery Project should capture:

-   opportunity
-   final delivery team
-   project status
-   lightweight completion information

------------------------------------------------------------------------

# 19. Legacy Code Pruning

Audit and remove/retire:

### Obsolete lifecycle actions

Examples to search for:

``` text
reject
rework
old stage transition
direct stage mutation
generic stage PATCH
```

### Duplicate POC APIs

The current inspected baseline contains both newer Phase 2 POC/phase2
routes and older-looking `poc_routes`.

Do not leave both competing implementations.

Determine which one is authoritative, migrate callers, then remove the
obsolete route/service/model.

### Obsolete closure APIs

Inspect old actions such as:

``` text
reject-closed-won
```

and remove them if they contradict the frozen closure workflow.

Do not retain dead endpoints simply for compatibility unless a real
consumer exists.

------------------------------------------------------------------------

# 20. Backend Tests

Add/update tests for:

### Assignment

-   PSM can assign SE.
-   Non-PSM cannot assign SE.
-   Invalid role candidate rejected.
-   Duplicate assignment prevented.
-   Closed opportunity cannot be assigned.

### RFX

-   Assigned SE can enter RFX.
-   Sales Executive cannot.
-   RFX Drive link can be stored.
-   Drive permissions are not falsely claimed as verified.

### POC

-   First POC requires DM assignment.
-   DM can assign max two allowed POC members.
-   Repeat POC does not require DM.
-   Repeat request notifies existing DE/DA.
-   Repeat request requires reason.
-   History is immutable.
-   Submitted result remains immutable.

### No POC closure

-   SE can request Closed Won from Qualified.
-   SE can request Closed Lost from Qualified.
-   SE can request Closed Won from RFX.
-   SE can request Closed Lost from RFX.
-   Request goes to PSM.
-   SE cannot directly approve their own request.
-   Unauthorized role denied.

### Closed outcomes

-   Authorized Closed Won at permitted stages.
-   Authorized Closed Lost at permitted stages.
-   Closed opportunity locked.
-   Delivery Manager notified on every Closed Won.

### Concurrency

Every sensitive mutation must test stale `row_version` and return `409`.

------------------------------------------------------------------------

# 21. Backend Definition of Done

No duplicate state machine.

No duplicate POC architecture.

No obsolete closure route.

No dead RFX/POC requirement fields.

No frontend-only authorization.

All business mutations go through explicit domain actions.

Full test suite passes.
