# Deal Room V2 --- Database and Migration Specification

## 1. Migration Strategy

All persistent schema changes must use Alembic / Flask-Migrate.

Never manually modify the database schema.

Before migration:

1.  inspect current models
2.  inspect current migrations
3.  inspect live database
4.  identify data dependencies
5.  remove application callers first
6.  create migration
7.  upgrade clean database
8.  upgrade representative existing database
9.  run tests

------------------------------------------------------------------------

# 2. Opportunity Team / Solution Engineer Assignment

Reuse the existing opportunity-team representation if it is
authoritative.

Do not create a second:

``` text
solution_engineer_assignments
```

table if `OpportunityTeam` already models the relationship correctly.

Required semantics:

``` text
opportunity
    ↓
opportunity_team
    ↓
user
    +
role = Solution Engineer
```

Backend must validate that the assigned user possesses the Solution
Engineer system role.

------------------------------------------------------------------------

# 3. RFX Context

Keep a lightweight RFX context.

Recommended persisted data:

``` text
opportunity_id
drive_folder_link
created_by
created_at
updated_by
updated_at
row_version
```

Remove/deprecate fields that duplicate external documents.

Do not store:

``` text
RFP file content
RFQ file content
POC agreement file content
technical document content
success criteria
exit criteria
POC objective
```

Those belong in Google Drive.

------------------------------------------------------------------------

# 4. POC Model

There must be ONE authoritative POC model.

The current project history references:

``` text
poc
poc_tracker
```

The implementation must determine which is authoritative.

If `poc_tracker` is the current V2 source of truth, retire the old `poc`
table/model/routes/services.

Do not maintain both.

------------------------------------------------------------------------

# 5. POC Fields to Remove or Deprecate

The new workflow no longer requires database-owned copies of:

``` text
objective
success_metric
exit_criteria
failure_condition
POC agreement fields
RFP/RFQ fields
technical requirement fields
```

Before dropping any column:

``` text
Search backend
Search frontend
Search tests
Search seed scripts
Search reports/dashboard queries
Search migrations
```

Only then remove.

If a field is no longer part of the domain contract, prefer removing it
rather than leaving permanent dead schema.

------------------------------------------------------------------------

# 6. POC History

If no suitable immutable history table exists, create:

``` text
poc_history
```

Suggested schema:

  Column           Purpose
  ---------------- -------------------------------
  history_id       Primary key
  opportunity_id   Opportunity reference
  actor_id         User who performed the action
  event_type       Business event
  reason           Reason for repeat POC
  created_at       Immutable timestamp

Optional:

``` text
metadata JSONB
```

only if the existing architecture already uses this safely and
consistently.

Do not store Drive documents or demo files.

------------------------------------------------------------------------

# 7. POC History Event Types

At minimum:

``` text
POC_STARTED
POC_SUBMITTED
NEW_POC_REQUESTED
```

The critical event is:

``` text
NEW_POC_REQUESTED
```

which must store:

``` text
actor
timestamp
reason
```

History is append-only.

Do not update old history rows to represent a new attempt.

------------------------------------------------------------------------

# 8. Closure Approval Request

A new persisted closure-request structure may be required.

Before adding it, inspect whether the existing system already has an
approval/request entity that can represent this safely.

If none exists, use something conceptually like:

``` text
closure_requests
----------------
request_id
opportunity_id
requested_by
requested_outcome
reason
status
reviewed_by
reviewed_at
created_at
row_version
```

Statuses:

``` text
Pending
Approved
Rejected
Cancelled
```

The exact names should follow existing project conventions.

Purpose:

``` text
Solution Engineer
    ↓
closure_requests
    ↓
Pre-Sales Manager
    ↓
approve/reject
```

Do not add a generic approval framework if the existing architecture
already provides one suitable for this domain.

------------------------------------------------------------------------

# 9. Closure Request Constraints

Database/application rules:

``` text
requested_outcome IN (
    Closed Won,
    Closed Lost
)
```

For Closed Lost:

``` text
reason IS NOT NULL
```

if required by the frozen closure policy.

A closure request does not itself close the opportunity.

Only the authorized approval action changes:

``` text
outcome
operational_status
```

------------------------------------------------------------------------

# 10. Concurrency

Sensitive records must retain/use:

``` text
row_version
```

At minimum:

-   Opportunity
-   POC
-   closure request where concurrent review matters

Do not introduce a second concurrency mechanism.

------------------------------------------------------------------------

# 11. Delivery Project

Reuse the existing:

``` text
delivery_projects
delivery_project_members
```

Do not create a second delivery project structure.

When Closed Won occurs:

``` text
delivery_project
```

can be created/activated according to the existing architecture.

If POC members exist, they can be used as suggested members.

They are not automatically finalized.

------------------------------------------------------------------------

# 12. Notifications

Do not create a database-specific second notification table if the
current `notifications` system is authoritative.

New domain events should flow through the existing event/notification
mechanism.

Required events should include:

``` text
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

Reuse existing names where equivalent events already exist.

Avoid duplicate events.

------------------------------------------------------------------------

# 13. Data Migration / Seed Changes

Seed/reset scripts must stop generating obsolete POC fields as required
business data.

Remove seeded values for fields that are being deleted.

Create realistic scenarios:

### Scenario A

``` text
Qualified
No POC
Closure request → Closed Won
```

### Scenario B

``` text
RFX
No POC
Closure request → Closed Lost
```

### Scenario C

``` text
RFX
POC
First POC team assigned
```

### Scenario D

``` text
POC
New POC requested
Reason stored
Existing DE/DA notified
```

### Scenario E

``` text
POC
Closed Won
Delivery Manager notified
POC team pre-selected
```

### Scenario F

``` text
RFX
Closed Won
No POC team
Delivery team starts empty
```

------------------------------------------------------------------------

# 14. Database Tests

Verify:

-   one authoritative POC structure
-   no duplicate POC source of truth
-   POC history append-only
-   repeat POC reason required
-   closure request does not directly close opportunity
-   Closed Won/Lost stored as outcomes
-   lifecycle stage remains unchanged when closure occurs
-   closed opportunity locked
-   row_version increments correctly
-   delivery project references correct opportunity
-   POC team can be used as suggested delivery team

------------------------------------------------------------------------

# 15. Database Definition of Done

Migration upgrade succeeds on a clean database.

Migration upgrade succeeds against a representative current database.

No obsolete POC table remains if it has been explicitly retired.

No dead POC requirement columns remain unless deliberately retained as a
documented compatibility field.

No duplicate assignment model exists.

No duplicate notification model exists.

Seed/reset produces only valid V2 states.
