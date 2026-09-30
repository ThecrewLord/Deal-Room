# Deal Room V2 --- Frontend Change Specification

## 1. Objective

Redesign the opportunity/RFX/POC UI around the revised workflow.

The frontend must not preserve obsolete fields merely because the
backend currently exposes them.

The frontend must consume the authoritative backend API only.

Never use UI hiding as the security mechanism.

------------------------------------------------------------------------

# 2. Opportunity Detail --- Remove Redundant POC Fields

Remove the following from Opportunity Detail / POC cards:

``` text
POC Objective
Success Metrics
Exit Criteria
Technical Requirements
POC Agreement fields
RFP/RFQ content fields
```

These documents are maintained in the RFX Google Drive folder.

Instead show:

``` text
RFX Documents
[ Open RFX Drive Folder ]
```

with a clear disclaimer:

> Google Drive is used for opportunity documents and demo artifacts.
> Deal Room does not verify Google Drive permissions.

------------------------------------------------------------------------

# 3. RFX UI

The RFX section should show:

``` text
RFX

Google Drive Folder
[ Open Drive Folder ]

Documents are maintained externally in Google Drive.
```

The application should not attempt to render or duplicate:

-   RFP
-   RFQ
-   POC agreement
-   client signed documents
-   technical documents

------------------------------------------------------------------------

# 4. Solution Engineer Assignment

After the Sales Manager approves the Lead:

``` text
Qualified
    ↓
Pending Pre-Sales Assignment
```

The Pre-Sales Manager sees a queue of opportunities requiring SE
assignment.

UI:

``` text
Opportunity
Sales Owner
Account
Stage
Created By

[ Assign Solution Engineer ]
```

Candidate list must contain only users who actually have the Solution
Engineer role.

The frontend must not assume a user is eligible based only on a name or
UI role label.

------------------------------------------------------------------------

# 5. Solution Engineer Opportunity View

Once assigned, the SE sees:

``` text
Opportunity
Account
Sales information
Stakeholders
OEMs
RFX
POC
Activities
Follow-ups
```

The technical stage controls should be explicit.

At Qualified:

``` text
[ Move to RFX ]
```

At RFX:

``` text
[ Move to POC ]
```

The backend remains authoritative.

------------------------------------------------------------------------

# 6. RFX → POC

When the SE clicks:

``` text
Move to POC
```

the frontend must:

1.  Send the current `row_version`.
2.  Verify/use the existing RFX Drive link.
3.  Call the explicit backend transition.
4.  Handle `409` concurrency.
5.  Refresh opportunity state after success.

Do not create a frontend-only stage update.

------------------------------------------------------------------------

# 7. POC Card

The POC card should be lightweight.

Example:

``` text
POC
────────────────────────────────
Status: In Progress

POC Team
• DevOps Engineer — Raj
• Data Analyst — Aman

Current Demo
[ Open Demo ]

[ Submit / Update Demo ]

POC History
────────────────────────────────
23 Sep
New POC requested

Reason:
Client requested API integration.

Requested by:
Solution Engineer
────────────────────────────────

[ Request New POC ]
```

Do not display document fields that belong in the RFX Drive.

------------------------------------------------------------------------

# 8. First POC

The first POC flow:

``` text
Solution Engineer
      ↓
POC stage
      ↓
Delivery Manager
      ↓
Assign DE / DA
```

The POC card should show assignment status.

If no team is assigned yet:

``` text
Awaiting Delivery Manager assignment
```

Only the Delivery Manager sees the assignment action.

------------------------------------------------------------------------

# 9. Repeat POC

When the SE determines that another demo is needed:

Show:

``` text
Request New POC
```

Clicking it opens:

``` text
Why is another POC required?

[ textarea ]

[ Cancel ] [ Request New POC ]
```

Reason is mandatory.

After success:

``` text
New POC requested.
The existing POC team has been notified.
```

Do not show a Delivery Manager assignment workflow.

------------------------------------------------------------------------

# 10. POC History

History should be lightweight.

Show:

``` text
POC History

Attempt 1
Date: ...
Reason: ...
Requested by: ...

Attempt 2
Date: ...
Reason: ...
Requested by: ...
```

Do not attempt to display every historical demo/document.

The Drive remains the artifact repository.

------------------------------------------------------------------------

# 11. Demo Submission

DE/DA should see:

``` text
POC Demo

Drive View Link
[ ______________________________ ]

[ Submit Demo ]
```

The frontend should validate basic URL input but backend validation
remains authoritative.

After submission:

``` text
Demo submitted.
Solution Engineer has been notified.
```

------------------------------------------------------------------------

# 12. Solution Engineer Review

After submission:

``` text
POC Demo
[ Open Demo ]

[ Request New POC ]
```

The SE can review and present the demo.

If changes are needed:

``` text
Reason
[ ______________________________ ]

[ Request New POC ]
```

------------------------------------------------------------------------

# 13. No-POC Closure

If the SE decides that a POC is not required:

At Qualified or RFX show:

``` text
[ Request Closure Approval ]
```

Dialog:

``` text
Request Closure Approval

Outcome:
( ) Closed Won
( ) Closed Lost

Reason:
[ required for Closed Lost ]

[ Cancel ] [ Submit Request ]
```

The frontend should clearly state:

``` text
This sends a closure request to the Pre-Sales Manager.
The opportunity is not closed until the request is approved.
```

The SE must not see a UI action that directly bypasses PSM approval.

------------------------------------------------------------------------

# 14. PSM Closure Queue

Pre-Sales Manager needs a clear queue:

``` text
Closure Approval Requests
```

Each row:

``` text
Opportunity
Current Stage
Requested Outcome
Requested By
Requested At

[ Review ]
```

Review view:

``` text
Closure Request

Opportunity: ...
Current Stage: Qualified / RFX
Requested by: Solution Engineer
Requested outcome: Closed Won / Closed Lost

[ Approve ]
[ Reject Request ]
```

If the request is rejected, the opportunity remains open.

Do not confuse "reject closure request" with the obsolete Lead
Reject/Rework workflow.

------------------------------------------------------------------------

# 15. Negotiations

The SE manually controls entry into Negotiations.

At POC:

``` text
[ Move to Negotiations ]
```

only when the backend permits it.

Do not automatically show:

``` text
POC submitted → Negotiations
```

as an automatic transition.

------------------------------------------------------------------------

# 16. Delivery Handoff

When Closed Won:

Delivery Manager receives a notification.

Delivery Project UI:

### If POC team exists

``` text
Suggested Delivery Team

☑ DevOps Engineer — Raj
☑ Data Analyst — Aman

[ Approve Team ]
[ Change Team ]
```

### If no POC team exists

``` text
Delivery Team

No team members selected.

[ Select Delivery Team ]
```

The DM finalizes the team.

------------------------------------------------------------------------

# 17. Closed Won / Closed Lost UI

Do not display Closed Won/Lost as ordinary lifecycle stages.

Display:

``` text
Stage: RFX
Outcome: Closed Won
Status: Closed
```

or:

``` text
Stage: POC
Outcome: Closed Lost
Status: Closed
```

The UI must make clear that the outcome can occur from the current
lifecycle stage.

------------------------------------------------------------------------

# 18. Universal Closure Display

Every opportunity should be able to show:

``` text
Lifecycle Stage
Outcome
Operational Status
```

separately.

Example:

``` text
Stage: Qualified
Outcome: Closed Won
Status: Closed
```

This is valid.

------------------------------------------------------------------------

# 19. Remove Old Frontend Components

Search and remove/retire:

``` text
Reject Lead
Rework
POC Objective
POC Success Metrics
POC Exit Criteria
POC Agreement input
Technical POC requirement forms
Duplicate POC cards
Old POC routes
Old Delivery role references
Direct stage mutation UI
Old closure actions
```

Do not merely hide them with CSS.

Remove their imports, API calls, state, validation, and dead components.

------------------------------------------------------------------------

# 20. API Layer

Frontend API services must have explicit functions such as:

``` text
assignSolutionEngineer()
moveOpportunityToRfx()
moveOpportunityToPoc()
requestNewPoc()
submitPocResult()
requestClosureApproval()
approveClosure()
createDeliveryProject()
finalizeDeliveryTeam()
```

Names should follow existing project conventions.

Do not expose a generic:

``` text
updateOpportunity(stage=...)
```

for lifecycle mutations.

------------------------------------------------------------------------

# 21. Error Handling

Handle:

``` text
400 invalid input
401 authentication
403 authorization
404 not visible/not found
409 concurrency/state conflict
```

For `409`:

``` text
This opportunity was changed by someone else.
Refresh and try again.
```

Do not silently retry sensitive mutations.

------------------------------------------------------------------------

# 22. Frontend Definition of Done

-   No obsolete POC requirement fields.
-   No duplicate POC UI.
-   No old Delivery role.
-   No direct stage mutation.
-   PSM assignment UI exists.
-   SE RFX/POC controls exist.
-   Repeat POC request UI exists.
-   POC history reason UI exists.
-   No-Poc closure approval UI exists.
-   PSM closure queue exists.
-   Delivery handoff UI correctly preselects POC team.
-   Closed Won/Lost displayed as outcomes.
-   Production build passes.
