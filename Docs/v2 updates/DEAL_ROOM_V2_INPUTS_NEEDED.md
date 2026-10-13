# Deal Room V2 --- Inputs Needed Before Implementation

## What is already defined

The business workflow is sufficiently defined to write the
implementation contract.

The current decisions are:

-   Pre-Sales Manager assigns Solution Engineer.
-   Solution Engineer owns technical progression.
-   RFX Drive folder is the external document source of truth.
-   POC documents/objective/success/exit information are not duplicated
    in Opportunity Detail.
-   First POC team is assigned by Delivery Manager.
-   Repeat POCs bypass Delivery Manager.
-   Existing DE/DA team is automatically notified for repeat POCs.
-   Repeat POC history stores the reason, actor, and timestamp.
-   Solution Engineer manually decides when to enter Negotiations.
-   If no POC is needed, SE can request PSM closure approval from
    Qualified or RFX.
-   PSM approves/rejects that closure request.
-   Closed Won / Closed Lost can occur at any authorized lifecycle
    stage.
-   Every Closed Won notifies Delivery Manager.
-   POC team members are suggested/pre-selected for Delivery when they
    exist.
-   Delivery Manager can approve/change the final Delivery team.
-   DE/DA unavailability is explicitly future scope and should NOT be
    implemented now.

## What I need from you

### 1. Latest source code

For exact file-level implementation, provide the **latest backend ZIP
and latest frontend/src ZIP** that you are actually running now.

This is important because the project has accumulated multiple phases
and historical implementations. The available project documentation
identifies overlapping/legacy-looking POC APIs and older assignment
implementations, but the exact current source is needed before deciding
precisely which files/classes/routes can be deleted.

### 2. Current database state

Provide either:

-   the current database schema dump, or
-   access to the current local database through the supplied
    project/environment.

A schema-only PostgreSQL dump is enough.

This is needed before writing a destructive migration that removes
obsolete POC columns/tables.

### 3. One clarification I recommend

Confirm the exact behavior of a rejected closure request:

``` text
SE requests Closed Won/Lost
        ↓
PSM rejects request
        ↓
Opportunity remains Open at same stage
```

This is the behavior assumed in these documents.

No new business rule is otherwise required from you.

## What does NOT need to be provided

You do not need to provide:

-   another flowchart
-   another business specification
-   old Phase 1/2/3 prompts
-   old ZIPs if the latest source contains the current implementation

The latest source code + current database schema are the important
implementation inputs.
