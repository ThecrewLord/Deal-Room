# Deal Room V2 --- Workflow Change Set Master

## Purpose

This document is the implementation contract for the revised Deal Room
V2 opportunity workflow.

It covers:

-   Backend changes
-   Frontend changes
-   Database/migration changes
-   Legacy-code pruning
-   Authorization changes
-   POC iteration behavior
-   RFX/Google Drive behavior
-   Closure-request behavior
-   Delivery handoff
-   Testing and certification

The objective is **not** to add another layer on top of the existing
implementation.

The implementation must first identify and remove obsolete/duplicate
behavior, then modify the remaining authoritative workflow.

------------------------------------------------------------------------

# 1. FINAL BUSINESS WORKFLOW

``` text
Deal Finder
    ↓
Lead
    ↓
Sales Manager Review
    ├── Closed Won
    ├── Closed Lost
    └── Approve + Assign Sales Executive
            ↓
        Qualified
            ↓
    Pre-Sales Manager
            ↓
    Assign Solution Engineer
            ↓
    Solution Engineer
            ↓
           RFX
            ↓
       ┌────┴────┐
       │         │
    POC needed  No POC needed
       │         │
       ▼         ▼
      POC       SE requests
       │        PSM closure approval
       │         │
       │      ┌──┴──┐
       │      ▼     ▼
       │    Won    Lost
       │
       ▼
POC execution / iterations
       │
       ▼
Solution Engineer decides
when technically ready
       │
       ▼
Negotiations
       │
       ▼
Pre-Sales Manager final approval
       │
   ┌───┴────┐
   ▼        ▼
Won       Lost
   │
   ▼
Delivery Manager
   │
   ▼
Delivery Project
```

## Critical rule

**Closed Won and Closed Lost are outcomes, not lifecycle stages.**

They may occur at any authorized lifecycle stage.

The backend must not implement a single hard-coded "Closed Won only from
Negotiations" assumption.

------------------------------------------------------------------------

# 2. FINAL LIFECYCLE

The lifecycle remains:

``` text
Lead
Qualified
RFX
POC
Negotiations
Delivery
```

Outcomes:

``` text
Open
Closed Won
Closed Lost
```

Operational status:

``` text
Active
Stalled
Closed
```

A closed opportunity is locked.

------------------------------------------------------------------------

# 3. ROLE OWNERSHIP

## Deal Finder

-   Creates the opportunity.
-   Remains Deal Finder permanently.
-   Cannot be replaced by later assignment.

## Sales Manager

-   Reviews submitted Lead.
-   Approves.
-   Closes Won at the initial review when authorized.
-   Closes Lost at the initial review when authorized.
-   Assigns Sales Executive on approval.
-   Does not assign Solution Engineer.

## Pre-Sales Manager

Two distinct responsibilities:

1.  After Sales Manager approval, assigns the Solution Engineer to the
    opportunity.
2.  Provides final closure approval where the workflow requires PSM
    approval.

For a no-POC opportunity:

``` text
SE → Request Closure Approval → PSM → Closed Won/Lost
```

This request may occur while the opportunity is:

``` text
Qualified
```

or:

``` text
RFX
```

For the normal technical progression:

``` text
POC → Negotiations → PSM final approval
```

## Solution Engineer

Owns technical workflow after assignment.

Responsibilities:

-   Qualified → RFX
-   Manage RFX Drive folder reference
-   Decide whether POC is required
-   RFX → POC when POC is required
-   Review submitted demos
-   Present demos to client
-   Record why another POC is required
-   Request repeat POC
-   Manually decide when the opportunity is ready for Negotiations
-   Request PSM closure approval when no POC is required at
    Qualified/RFX

## Delivery Manager

Only:

-   Assigns the team for the **first POC**
-   Handles Delivery team assignment after Closed Won

The Delivery Manager has **no role in repeat POC requests**.

## DevOps Engineer / Data Analyst

-   Execute POC work externally.
-   Upload demo/result externally.
-   Add a view link to the POC card.
-   Submit.

## Pre-Sales Manager

-   Receives closure requests.
-   Provides final approval where required.

------------------------------------------------------------------------

# 4. RFX IS THE DOCUMENT WORKSPACE

The Google Drive RFX folder is the source of truth for
opportunity/technical documents.

It can contain:

-   RFP
-   RFQ
-   POC Agreement
-   Client-signed documents
-   POC objective
-   Success criteria
-   Exit criteria
-   Technical requirements
-   Supporting documents

Deal Room should store the Drive folder reference.

Deal Room should **not duplicate these document fields on Opportunity
Detail**.

The application does not verify Google Drive permissions.

Do not build Drive API permission verification.

------------------------------------------------------------------------

# 5. POC DESIGN

The POC implementation must be lightweight.

Deal Room stores:

-   POC workflow state
-   assigned POC team
-   current active demo/result view link
-   submission metadata
-   lightweight POC history
-   reason for requesting another POC

Deal Room does NOT store:

-   POC documents
-   RFP/RFQ content
-   POC agreement files
-   demo files
-   technical documents

Those remain in Drive.

------------------------------------------------------------------------

# 6. POC ITERATION

The first POC:

``` text
SE → POC
   ↓
DM assigns DE/DA
   ↓
DE/DA works
   ↓
DE/DA submits demo link
   ↓
SE reviews
```

If changes are required:

``` text
SE
 ↓
Enter reason
 ↓
Request New POC
 ↓
Existing DE/DA automatically notified
 ↓
DE/DA creates new demo
 ↓
Submit new view link
 ↓
SE notified
 ↓
SE reviews again
```

The Delivery Manager is NOT involved in repeat POCs.

## POC history

Only the history/reason is retained in Deal Room.

Example:

``` text
POC History

2026-09-23
Requested by: Solution Engineer
Reason:
"Client requested additional API integration."

2026-09-27
Requested by: Solution Engineer
Reason:
"Demo did not meet the latency requirement."
```

Previous demo/document artifacts remain in Drive and are not copied into
Deal Room.

------------------------------------------------------------------------

# 7. NO-POC CLOSURE

If the SE determines that no POC is required, the opportunity does not
need to enter POC.

At either Qualified or RFX:

``` text
Solution Engineer
      ↓
Request Closure Approval
      ↓
Pre-Sales Manager
      ↓
Closed Won / Closed Lost
```

This is a business action and should not be implemented by directly
setting:

``` python
opportunity.outcome = ...
```

from an arbitrary frontend/API request.

Use an explicit service/domain action.

------------------------------------------------------------------------

# 8. NEGOTIATIONS

Solution Engineer manually decides when the opportunity is ready for
Negotiations.

Do not automatically enter Negotiations merely because:

-   a POC was submitted
-   a POC succeeded
-   a demo link exists

The SE must explicitly initiate the transition.

Negotiations remains mandatory before Delivery.

------------------------------------------------------------------------

# 9. CLOSED WON → DELIVERY

Every Closed Won opportunity must notify the Delivery Manager,
regardless of the stage from which it was closed.

If a POC team existed:

``` text
POC Team
  ↓
pre-selected/suggested Delivery team
```

The members are suggestions only.

The Delivery Manager can:

-   approve the suggested team
-   change the team
-   choose a different team

If no POC team existed:

``` text
No members pre-selected.
```

The Delivery Manager selects the Delivery team.

The POC team must never be silently auto-assigned as the final Delivery
team.

------------------------------------------------------------------------

# 10. LEGACY PRUNING PRINCIPLE

Do not preserve obsolete code merely because it exists.

Before implementation:

1.  Identify duplicate workflow implementations.
2.  Identify old POC models/routes/services.
3.  Identify old stage transition endpoints.
4.  Identify old RFX/POC fields.
5.  Identify obsolete frontend fields/components.
6.  Identify tests asserting superseded behavior.
7.  Replace callers.
8.  Remove dead code.
9.  Remove obsolete migrations only when safe; use new migrations for
    live database changes.
10. Search the repository again for stale behavior.

Do not hide obsolete functionality behind frontend conditionals.

If a business action is obsolete, remove/retire its backend path too.

------------------------------------------------------------------------

# 11. REQUIRED CERTIFICATION

The implementation is complete only when:

-   Backend tests pass.
-   Frontend build passes.
-   Alembic migration passes.
-   Clean database reset/seed passes.
-   Direct API authorization tests pass.
-   Closed Won/Lost can be exercised at all authorized stages.
-   No-POC closure works from Qualified and RFX.
-   POC repeat request bypasses DM.
-   POC history reason is preserved.
-   RFX documents are not duplicated into Opportunity fields.
-   Closed Won always notifies DM.
-   Delivery team preselection behaves correctly.
-   Obsolete POC/RFX implementations are removed.
-   No duplicate lifecycle/state machine exists.
-   No duplicate notification/audit system exists.
