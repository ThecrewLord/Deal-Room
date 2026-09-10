# Deal Room V2 --- Backend → Frontend Handoff & Implementation Contract

## 1. Purpose

This document is the handoff contract for the teammate/agent responsible
for the **frontend implementation and integration** of Deal Room V2.

The backend is already implemented through **Phase 3**. The frontend
must now be brought into complete alignment with the backend, database
model, authorization rules, lifecycle, and business workflows.

**Important:** Do not treat the frontend as an isolated UI task.

If the frontend requires a backend/API/database capability that is
missing, incomplete, inconsistent, or incorrectly modeled, **you are
authorized and expected to modify the backend and database as
necessary**.

The final result must be a working full-stack system, not merely a
visually complete frontend.

------------------------------------------------------------------------

# 2. Technology Stack

## Backend

-   Flask
-   SQLAlchemy
-   Flask-Migrate / Alembic
-   PostgreSQL
-   Docker
-   JWT authentication
-   Flask-Bcrypt
-   Centralized `AuthorizationService`
-   Service / repository / controller architecture

## Frontend

-   React
-   Vite
-   Centralized CSS/theme tokens
-   Shared UI components

## Database

-   PostgreSQL
-   Alembic migrations
-   Current schema is the authoritative persistence layer
-   Do not bypass migrations for permanent schema changes

------------------------------------------------------------------------

# 3. Frozen Roles

The current role vocabulary is:

1.  Leadership
2.  Admin
3.  Sales Executive
4.  Sales Manager
5.  Pre-Sales Manager
6.  Solution Engineer
7.  Delivery Manager
8.  DevOps Engineer
9.  Data Analyst

The old generic **Delivery** role is deprecated and must NOT be
recreated.

## Leadership

Leadership is the root privileged role.

Leadership has company-wide business and governance visibility.

Leadership cannot be removed/demoted/revoked if doing so would leave the
system without a Leadership account.

## Admin

Admin is an access-administration role only.

Admin can:

-   approve access
-   manage users
-   assign/revoke allowed roles
-   manage delegated administration

Admin cannot:

-   create opportunities
-   view the business pipeline
-   view business dashboards
-   manage opportunity lifecycle
-   assign Admin roles
-   elevate themselves
-   manage Leadership

The frontend must never assume that an Admin is a business user.

------------------------------------------------------------------------

# 4. Active Role Isolation

A user may have multiple assigned roles.

The user selects exactly one **active role**.

Backend authorization is based on the active role.

Example:

A user has:

``` text
Sales Executive
Solution Engineer
```

If active role is:

``` text
Sales Executive
```

the frontend must behave as Sales Executive.

It must not expose Solution Engineer actions simply because that role is
also assigned to the user.

Changing the active role must update:

-   sidebar
-   dashboard
-   available actions
-   workflow controls
-   permissions
-   API behavior

The backend remains the final security boundary.

------------------------------------------------------------------------

# 5. Frozen Opportunity Lifecycle

The authoritative lifecycle is:

``` text
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

Terminal outcomes:

``` text
Closed Won
Closed Lost
```

Outcomes are NOT normal lifecycle stages.

Do not recreate old stages such as:

-   Qualification
-   Discovery
-   Proposal
-   Negotiation
-   Closed Won
-   Closed Lost

as the V2 lifecycle.

Do not introduce:

-   Reject
-   Rework
-   Pending Rework
-   generic Delivery stage/role

as new business concepts.

------------------------------------------------------------------------

# 6. Opportunity State Model

Frontend must keep these concepts separate:

``` text
lifecycle_stage
operational_status
outcome
review_status
```

Lifecycle:

``` text
Lead
Qualified
RFX
POC
Negotiations
Delivery
```

Operational status:

``` text
Active
Stalled
Closed
```

Outcome:

``` text
Open
Closed Won
Closed Lost
```

Review status:

``` text
Draft
Pending Sales Manager Review
Approved
```

Never infer one from another incorrectly.

For example:

``` text
Stalled != Closed Lost
Delivery != Closed Won
Closed Won != lifecycle stage
```

------------------------------------------------------------------------

# 7. Deal Finder

The person who creates/founds an opportunity is the immutable **Deal
Finder**.

Once created:

-   Deal Finder cannot be changed
-   frontend must not expose a normal edit control for Deal Finder
-   backend must reject tampered requests

Do not implement reassignment of Deal Finder.

------------------------------------------------------------------------

# 8. Lead Creation

Every approved active business role except Admin is eligible to create a
lead according to backend authorization.

Required creation information includes:

-   opportunity name
-   canonical account
-   initial Opportunity Value

Before submission for Sales Manager review:

-   description required
-   at least one stakeholder
-   pain points required

The frontend must show validation before submission, but backend
validation remains authoritative.

------------------------------------------------------------------------

# 9. Initial Sales Manager Review

The initial review has exactly three meaningful actions:

``` text
Approve
Close Won
Close Lost
```

Do NOT display:

-   Reject
-   Rework
-   Return to Sales Executive

## Approve

Sales Manager:

-   approves the opportunity
-   assigns Sales Executive
-   opportunity becomes Qualified

Sales Manager may approve their own lead if they are the Deal Finder.

## Close Won

Allowed during initial Lead review according to authorization.

No Sales Executive assignment is required for direct closure.

## Close Lost

Allowed during initial Lead review according to authorization.

Closed Lost requires a reason.

If reason is `Other`, an explanation is mandatory.

------------------------------------------------------------------------

# 10. Post-Qualified Workflow

After Qualified:

Sales Manager and Sales Executive do not gain generic stage-edit
authority.

Stage authority is controlled by:

-   Pre-Sales Manager
-   assigned Solution Engineer
-   Leadership

The frontend must not render a generic:

``` text
Change Stage
```

dropdown for every role.

Use explicit workflow actions such as:

``` text
Advance to RFX
Advance to POC
Advance to Negotiations
```

only when the backend says the action is permitted.

------------------------------------------------------------------------

# 11. RFX

Entering RFX does NOT require a Drive link.

The Drive link becomes mandatory for:

``` text
RFX → POC
```

The RFX Drive context persists across POC cycles.

The application must not claim that Google Drive permissions have been
verified.

Use a disclaimer such as:

> Confirm that the required users have appropriate access to the Google
> Drive resource. Deal Room does not verify Drive permissions.

------------------------------------------------------------------------

# 12. POC

POC is a first-class workflow.

POC supports multiple historical cycles.

Required POC request information includes:

-   objective
-   success metrics
-   exit criteria
-   input Drive link
-   target date
-   failure condition

POC status and cycle history must remain visible.

The frontend must not assume that an opportunity has only one POC
forever.

------------------------------------------------------------------------

# 13. POC Team

POC team assignment is handled by the Delivery Manager.

Maximum:

``` text
2 members
```

Allowed POC member roles:

-   DevOps Engineer
-   Data Analyst

Do NOT introduce the old Delivery role.

The frontend must prevent selecting more than two members, but the
backend must also enforce the limit.

------------------------------------------------------------------------

# 14. POC Execution

Deal Room does not execute the POC itself.

The POC team works externally.

Deal Room records:

-   assignment
-   execution status
-   input link
-   result/view link
-   submission metadata
-   outcome
-   notes
-   timestamps

Once submitted, POC result information is treated as
historical/immutable.

Do not provide normal deletion/edit controls for submitted results.

------------------------------------------------------------------------

# 15. POC Notifications

Important mapping:

``` text
POC_REQUESTED → Delivery Manager
```

Do not change this to Pre-Sales Manager.

The frontend notification center must display the notification
correctly.

------------------------------------------------------------------------

# 16. Negotiations

Negotiations is mandatory:

``` text
POC → Negotiations → Delivery
```

There is no:

``` text
POC → Delivery
```

or:

``` text
RFX → Negotiations
```

Negotiation context is lightweight.

Optional commercial documents:

-   NDA
-   MSA
-   SOW

NDA may be suggested.

Do not turn this into a full contract-management system.

------------------------------------------------------------------------

# 17. Closed Won

Final Closed Won approval at Negotiations belongs to:

-   Pre-Sales Manager
-   Leadership

Not Sales Manager.

When Closed Won is completed:

1.  outcome becomes `Closed Won`
2.  operational status becomes `Closed`
3.  Final Revenue = current Opportunity Value
4.  Delivery Project is created
5.  Opportunity becomes locked

------------------------------------------------------------------------

# 18. Closed Lost

Closed Lost requires:

-   reason

If reason is:

``` text
Other
```

then explanation is mandatory.

The persisted closure remark is expected to use the existing:

``` text
lost_explanation
```

field unless backend inspection proves otherwise.

Frontend label should be:

``` text
Closed Lost Remark
```

or:

``` text
Closure Remark
```

Closed opportunities are locked.

------------------------------------------------------------------------

# 19. Opportunity Value / Revenue

Opportunity Value:

-   initial value is set by Deal Finder
-   later current value changes are restricted to authorized roles

Every value change records:

``` text
old value
new value
reason
actor
timestamp
```

Use the value history endpoint for historical display.

At Closed Won:

``` text
Final Revenue = Current Opportunity Value
```

Final Revenue becomes immutable.

Do not add:

-   commission calculation
-   incentive calculation
-   hidden revenue adjustment

------------------------------------------------------------------------

# 20. Revenue Attribution

Sourced Revenue:

Revenue from opportunities where the employee is the immutable Deal
Finder.

Participation Revenue:

Revenue according to the already-defined participation model.

Do not invent a new attribution formula in the frontend.

If the backend response is insufficient to render the approved
attribution view:

1.  inspect backend service/repository
2.  determine whether the required field/query is missing
3.  implement the backend change
4.  create an Alembic migration if persistence is required
5.  test it
6.  then consume it in the frontend

Do not hardcode revenue numbers.

------------------------------------------------------------------------

# 21. Accounts

Accounts are a separate domain.

Account statuses:

``` text
Active
Archived
Banned
```

Rules:

-   canonical identity is authoritative
-   duplicates must be prevented
-   uniqueness applies across active, archived and banned accounts
-   archived accounts cannot be reactivated
-   banned accounts cannot be selected for new opportunities
-   banned account creation/selection must produce exactly:

``` text
this account is banned
```

Do not create an inline Account creation form inside Create Opportunity.

Account management remains a separate page.

Account rows should NOT become links into the opportunity pipeline.

------------------------------------------------------------------------

# 22. Stakeholders

Stakeholder fields:

-   name
-   job title
-   email
-   phone
-   company
-   tags

Fixed tags:

-   Economic Buyer
-   Technical Champion
-   End User
-   Blocker
-   Decision Maker

A stakeholder can have multiple tags.

An opportunity can have:

``` text
0 or 1 Decision Maker
```

Never allow two Decision Makers.

The backend enforces this transactionally/database-side.

Sales Executive can add/manage stakeholders where authorized but cannot
arbitrarily edit protected identity fields.

Closed opportunities cannot have stakeholder/tag mutations.

------------------------------------------------------------------------

# 23. OEM Registry

Everyone may see OEM names where authorized.

Employees must NOT receive:

-   contact person
-   email
-   phone

Leadership may see full OEM details and has OEM governance privileges.

This restriction is backend enforced.

Frontend must not assume that hiding a field with CSS is security.

Opportunity-OEM associations support multiple OEMs.

------------------------------------------------------------------------

# 24. Delivery Project

Delivery Project is a separate aggregate.

Do NOT represent Delivery Project merely as:

``` text
opportunity.delivery = true
```

It has its own identity and state.

It contains:

-   project ID
-   opportunity reference
-   account
-   Delivery Manager
-   status
-   members
-   completion
-   timestamps
-   history

POC team members may be proposed for Delivery.

They are NOT blindly auto-assigned.

Delivery Manager can:

-   add members
-   remove members
-   reassign members
-   accept proposed members
-   complete project

There is no artificial maximum number of Delivery Project members.

------------------------------------------------------------------------

# 25. Activities

Activities are NOT AuditLog.

Supported types:

-   Call
-   Meeting
-   Email
-   Note
-   Interaction

Activity contains:

-   opportunity
-   type
-   summary
-   actor
-   timestamp
-   optional follow-up context

Use Activities for business interactions.

Use AuditLog for system/history/security auditing.

Never merge these domains in the frontend data model.

------------------------------------------------------------------------

# 26. Follow-ups

Follow-up contains:

-   opportunity
-   owner
-   due date
-   description/task
-   status
-   creator
-   completion timestamp

Statuses:

``` text
Open
Completed
Overdue
```

Overdue is derived from due date and completion state.

Frontend should provide:

-   Due Today
-   Upcoming
-   Overdue
-   Completed

Do not create a second task/follow-up system.

------------------------------------------------------------------------

# 27. Notifications

Existing notification framework is authoritative.

Important events include:

-   Qualified
-   Solution Engineer assigned
-   RFX entered
-   POC requested
-   POC assigned
-   POC submitted
-   POC ready for review
-   Negotiations entered
-   Closed Won
-   Closed Lost
-   Delivery Project created
-   Delivery assignment
-   Follow-up due
-   Follow-up overdue

Current API supports:

``` http
GET /api/notifications
POST /api/notifications/<notification_id>/read
```

Unread filtering is available.

Do not build a separate notification storage system.

------------------------------------------------------------------------

# 28. Audit / History

Audit history must be treated as read-only.

Important events include:

-   lifecycle changes
-   closure
-   value changes
-   assignments
-   stakeholder changes
-   OEM associations
-   POC changes
-   Negotiation approval
-   Delivery Project changes
-   account governance
-   access/role administration

Do not create frontend controls that edit/delete audit history.

------------------------------------------------------------------------

# 29. Global Search

Current backend search endpoint:

``` http
GET /api/search?q=<query>&type=<optional>
```

Current supported search types in the inspected backend implementation
are:

``` text
opportunity
account
poc
```

Current search behavior:

-   minimum 2 characters
-   maximum 100 characters
-   maximum 25 returned results
-   server-side authorization
-   Admin receives no business search results
-   opportunity search is authorization scoped
-   account search is authorization scoped
-   POC search is scoped through visible opportunities

### Important frontend instruction

Do not assume that every entity is currently supported by the search API
just because the product specification mentions Activities, Follow-ups,
OEMs, Stakeholders or Delivery Projects.

Before implementing additional search categories:

1.  inspect the backend
2.  determine whether the endpoint supports them
3.  if missing and required by the product UX, implement the backend
    capability
4.  add tests
5.  add DB indexes if necessary
6.  only then integrate it in the frontend

Do not fake unsupported search categories with client-side filtering of
already-loaded pages.

------------------------------------------------------------------------

# 30. Current Dashboard API

Primary dashboard endpoint:

``` http
GET /api/dashboard
```

Response currently includes fields such as:

``` json
{
  "total_opportunities": 0,
  "total_pipeline_value": 0,
  "weighted_forecast": 0,
  "open_opportunities": 0,
  "closed_won": 0,
  "closed_lost": 0,
  "conversion_rate": 0,
  "stage_ageing": [],
  "average_stage_ageing": 0,
  "stalled_deals": 0,
  "active_pocs": 0,
  "win_loss_ratio": 0,
  "partner_contribution": 0,
  "pipeline_by_stage": [],
  "recent_opportunities": [],
  "upcoming_pocs": [],
  "recent_activity": []
}
```

Dashboard metrics are backend-derived.

Do not hardcode dashboard values.

------------------------------------------------------------------------

# 31. Dashboard Lifecycle

Pipeline funnel must use:

``` text
Lead
Qualified
RFX
POC
Negotiations
Delivery
```

Do not count Closed Won or Closed Lost as lifecycle stages.

Dashboard must distinguish:

``` text
stage
status
outcome
```

------------------------------------------------------------------------

# 32. Role-Specific Dashboards

## Leadership

Company-wide:

-   pipeline
-   weighted forecast
-   revenue
-   win/loss
-   conversion
-   stage ageing
-   stalled opportunities
-   POCs
-   delivery projects
-   team performance

## Admin

Access/governance only.

Do not show:

-   pipeline
-   revenue
-   opportunities
-   forecasts
-   business funnel

## Sales Manager

Focus on:

-   team pipeline
-   Sales Executive performance
-   reviews
-   revenue
-   win/loss
-   stalled deals
-   overdue follow-ups

## Sales Executive

Focus on:

-   own opportunities
-   own pipeline
-   activities
-   stakeholders
-   follow-ups
-   pending actions

## Pre-Sales Manager

Focus on:

-   technical pipeline
-   POC requests
-   POC assignments
-   POC reviews
-   Negotiations
-   technical team workload

## Solution Engineer

Focus on:

-   assigned opportunities
-   RFX
-   POC
-   POC results
-   Negotiations
-   technical activities
-   follow-ups

## Delivery Manager

Focus on:

-   active Delivery Projects
-   proposed POC team
-   project members
-   reassignment
-   completion

## DevOps Engineer / Data Analyst

Keep visibility limited to authorized POC work and relevant assigned
operational information.

------------------------------------------------------------------------

# 33. Performance APIs

Sales Manager:

``` http
GET /api/sales-manager/team-performance
GET /api/sales-manager/team-performance/<employee_id>
```

Pre-Sales Manager:

``` http
GET /api/pre-sales-manager/team-performance
GET /api/pre-sales-manager/team-performance/<employee_id>
```

These should only be shown where the active role and authorization
permit them.

------------------------------------------------------------------------

# 34. Important Existing API Areas

The current backend contains API groups for:

``` text
/auth
/opportunities
/accounts
/stakeholders
/oem
/poc
/phase2
/dashboard
/search
/notifications
/activity
/solution-design
/sales-manager/team-performance
/pre-sales-manager/team-performance
```

The `/api/phase2/...` endpoints currently cover several collaboration
domains including:

-   tags
-   opportunity-OEM associations
-   RFX
-   POCs
-   POC team
-   Negotiations
-   Delivery Project
-   activities
-   follow-ups

Inspect the actual route/controller/service before integrating.

------------------------------------------------------------------------

# 35. Opportunity APIs

Important existing routes include:

``` http
GET    /api/opportunities
GET    /api/opportunities/<id>
POST   /api/opportunities
PUT    /api/opportunities/<id>

POST   /api/opportunities/<id>/submit-lead
GET    /api/opportunities/review-queue
POST   /api/opportunities/<id>/review

POST   /api/opportunities/<id>/advance-to-rfx
POST   /api/opportunities/<id>/advance-to-poc
POST   /api/opportunities/<id>/advance-to-negotiations

POST   /api/opportunities/<id>/value
GET    /api/opportunities/<id>/value-history
GET    /api/opportunities/<id>/stage-history

POST   /api/opportunities/<id>/request-closed-won
POST   /api/opportunities/<id>/approve-closed-won
POST   /api/opportunities/<id>/close-won
POST   /api/opportunities/<id>/close-lost

POST   /api/opportunities/<id>/mark-stalled
POST   /api/opportunities/<id>/mark-active
```

Before using any endpoint, inspect its request/response schema.

Do not guess payload names.

------------------------------------------------------------------------

# 36. Explicit Backend + Database Responsibility

## THIS IS IMPORTANT

The frontend developer/agent is NOT restricted to frontend-only changes.

If you discover that the UI requirement cannot be implemented correctly
because the backend or database lacks required support:

**MAKE THE NECESSARY BACKEND AND DATABASE CHANGES.**

Examples:

-   missing API field
-   missing relation
-   missing persisted state
-   missing search index
-   missing history field
-   missing dashboard metric
-   missing notification event
-   missing authorization rule
-   missing database constraint
-   missing pagination
-   missing concurrency field
-   missing association table

Do not work around a missing backend capability with fake frontend
state.

------------------------------------------------------------------------

# 37. Database Change Rules

If a database change is required:

### Step 1

Inspect the current schema and Alembic head.

### Step 2

Confirm whether the required field/table/index/constraint already
exists.

### Step 3

If missing, create a new Alembic migration.

Example:

``` bash
flask db migrate -m "describe change"
flask db upgrade
```

Use the project's actual migration workflow if it differs.

### Step 4

Update SQLAlchemy models.

### Step 5

Update repositories/services/controllers/schemas as required.

### Step 6

Add or update tests.

### Step 7

Run migration against a clean database.

### Step 8

Run migration against the existing development database.

### Step 9

Run seed/reset.

### Step 10

Verify frontend integration.

**Never directly alter the PostgreSQL schema manually and leave the
change untracked by Alembic.**

Do not edit already-applied migrations to hide new schema changes.

------------------------------------------------------------------------

# 38. Database Integrity Requirements

Never solve a frontend problem by weakening database integrity.

Preserve:

-   one Decision Maker per opportunity
-   canonical account uniqueness
-   account lifecycle rules
-   POC team maximum
-   valid POC member roles
-   immutable/historical relationships
-   foreign keys
-   closed-record integrity
-   value history
-   Deal Finder immutability
-   lifecycle integrity

Use database constraints where the rule is fundamentally data integrity.

------------------------------------------------------------------------

# 39. Existing Phase 2 Database Domains

The current backend database contains/uses structures including:

``` text
accounts
opportunities
stakeholders
tags
stakeholder_tag_links

oem_partners
opportunity_oems

rfx_contexts
negotiation_contexts

poc_tracker
poc_team_members

delivery_projects
delivery_project_members

activities
follow_ups

opportunity_value_history
stage_history
audit_logs
notifications
```

Additional existing authentication/security structures include:

``` text
users
user_roles
user_system_permissions
token_blocklist
```

Do not create duplicate versions of these domains.

------------------------------------------------------------------------

# 40. POC Source of Truth

The V2 implementation uses:

``` text
poc_tracker
```

as the authoritative POC persistence structure.

Do not recreate the old duplicate `poc` table/domain as a frontend
requirement.

If code still references old compatibility structures, inspect whether
the reference is active runtime logic or historical compatibility.

------------------------------------------------------------------------

# 41. Frontend Authorization Pattern

The frontend should use authorization information to control UI.

However:

``` text
Frontend authorization = UX
Backend authorization = Security
```

Never assume that hiding a button makes the operation secure.

For every sensitive action:

1.  hide/disable action if unauthorized
2.  call backend
3.  handle 401
4.  handle 403
5.  handle validation errors
6.  handle concurrency errors
7.  refresh state after successful mutation

------------------------------------------------------------------------

# 42. Closed Opportunity UI

When closed:

``` text
outcome = Closed Won
```

or:

``` text
outcome = Closed Lost
```

and:

``` text
operational_status = Closed
```

Display a clear locked state.

Disable normal mutations.

For Closed Lost display:

``` text
Closed Lost Remark
```

Do not merely rely on disabled buttons.

The backend must still reject tampered requests.

------------------------------------------------------------------------

# 43. Concurrency

Sensitive records use optimistic concurrency.

Primary mechanism:

``` text
row_version
```

Frontend should send the version expected by the backend where the
endpoint requires it.

On conflict:

``` text
409 Conflict
```

or the project's established concurrency error.

Show a meaningful message such as:

> This record was updated by another user. Refresh and try again.

Do not silently overwrite newer data.

------------------------------------------------------------------------

# 44. Error Handling

Frontend must properly handle:

``` text
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
429 Rate Limit
500 Server Error
```

Do not display raw backend stack traces.

For known business errors, display the backend's message.

The exact banned account error is:

``` text
this account is banned
```

------------------------------------------------------------------------

# 45. Design System

Continue using the existing shared components and centralized design
tokens.

Expected components include:

-   PageHeader
-   Card
-   Button
-   EmptyState
-   StatusBadge
-   StageBadge
-   DataTable
-   SearchInput

Do not introduce an unrelated design language.

Do not duplicate:

-   sidebar user block
-   theme tokens
-   button systems
-   card systems
-   table systems

------------------------------------------------------------------------

# 46. Opportunity Detail Page

The Opportunity Details UI should organize:

## Overview

-   Opportunity
-   Account
-   Deal Finder
-   owners
-   lifecycle
-   operational status
-   outcome

## Commercial

-   Opportunity Value
-   Final Revenue when closed
-   value history where authorized

## Stakeholders

-   stakeholder list
-   tags
-   Decision Maker

## OEM

-   associated OEM names
-   appropriate field redaction

## RFX

-   context
-   Drive link
-   disclaimer

## POC

-   POC cycles
-   current POC
-   team
-   results
-   links

## Negotiations

-   NDA
-   MSA
-   SOW
-   notes
-   approval

## Delivery

-   Delivery Project
-   manager
-   members
-   completion

## Activities

## Follow-ups

## Audit/History

------------------------------------------------------------------------

# 47. No Generic CRUD UI

Do not create generic:

``` text
Edit Everything
Delete Everything
Change Stage
Assign Anyone
```

buttons.

Actions must correspond to business rules.

Prefer explicit actions:

``` text
Submit for Review
Approve
Close Won
Close Lost
Advance to RFX
Advance to POC
Advance to Negotiations
Request POC
Assign POC Team
Submit POC Result
Approve Closed Won
Complete Delivery
```

only when authorized.

------------------------------------------------------------------------

# 48. Search UX

Search should support:

-   minimum 2 characters
-   loading
-   no results
-   API error
-   result grouping
-   entity labels
-   navigation to authorized detail pages

Do not fetch the entire database into the browser.

Do not perform client-side authorization filtering.

------------------------------------------------------------------------

# 49. Dashboard UX

Every dashboard must have:

-   loading state
-   empty state
-   error state
-   correct role scope
-   correct metrics
-   consistent cards
-   useful visual hierarchy

Charts should be based on backend data.

Do not fabricate chart values.

------------------------------------------------------------------------

# 50. Seed / Demo Data

The backend has deterministic V2 seed/reset support.

Use the seeded data to test the frontend.

Expected representative states include:

-   Lead
-   Qualified
-   RFX
-   POC
-   Negotiations
-   Delivery
-   Closed Won
-   Closed Lost
-   Active
-   Stalled
-   follow-ups
-   overdue follow-ups
-   activities
-   POC cycles
-   Delivery Projects
-   revenue history

Do not create fake frontend-only records to make screens look populated.

If seed data is insufficient for a required frontend workflow:

**modify the backend seed data and database through the proper
code/migration path.**

------------------------------------------------------------------------

# 51. What NOT to Do

Do NOT:

-   rewrite the backend architecture without reason
-   create duplicate services
-   create duplicate POC models
-   create duplicate notification systems
-   create duplicate follow-up systems
-   bypass AuthorizationService
-   put authorization logic only in React
-   hardcode dashboard values
-   hardcode revenue
-   invent forecast percentages
-   add lifecycle stages
-   reintroduce Delivery role
-   add Reject/Rework
-   allow stage skipping
-   allow Deal Finder editing
-   expose OEM contacts to employees
-   allow multiple Decision Makers
-   mutate closed opportunities
-   delete audit history
-   use client-side filtering as a security boundary
-   manually alter PostgreSQL without an Alembic migration
-   edit an already-applied migration to hide a change
-   create unnecessary database tables for UI-only concerns

------------------------------------------------------------------------

# 52. Required Frontend Workflow

Follow this order.

## Step 1 --- Inspect

Understand:

-   backend routes
-   schemas
-   response payloads
-   authorization
-   models
-   database
-   seed data

## Step 2 --- Build API client layer

Centralize API calls.

Do not scatter raw `fetch()` calls throughout components.

## Step 3 --- Build authentication/active-role handling

Ensure all API calls use the correct access token.

## Step 4 --- Build navigation

Role-correct sidebar and routes.

## Step 5 --- Build dashboards

Start with backend-provided metrics.

## Step 6 --- Build search

Use backend search.

## Step 7 --- Build Opportunity Details

Use domain sections.

## Step 8 --- Build workflow controls

Only show authorized actions.

## Step 9 --- Build collaboration pages

-   Accounts
-   Stakeholders
-   OEM
-   POC
-   Negotiations
-   Delivery
-   Activities
-   Follow-ups
-   Notifications

## Step 10 --- Integrate error/concurrency states

## Step 11 --- Test role-by-role

## Step 12 --- Fix backend/database gaps discovered during integration

## Step 13 --- Run full regression

------------------------------------------------------------------------

# 53. Full-Stack Rule

When something does not work, diagnose the complete chain:

``` text
UI
 ↓
API client
 ↓
HTTP request
 ↓
route
 ↓
controller
 ↓
service
 ↓
authorization
 ↓
repository
 ↓
SQLAlchemy
 ↓
PostgreSQL
```

Do not assume the frontend is always the problem.

Likewise, do not assume the backend is always the problem.

Find the actual failing layer.

------------------------------------------------------------------------

# 54. Database-First Rule for New Requirements

If a feature requires persistent state, ask:

> Where is the authoritative source of truth?

If it does not exist:

1.  design the data model
2.  add SQLAlchemy model
3.  add Alembic migration
4.  add constraints/indexes
5.  implement repository/service
6.  implement API
7.  add tests
8.  integrate frontend

Never store business-critical state only in React state/localStorage.

------------------------------------------------------------------------

# 55. API Contract Rule

Before consuming an endpoint, inspect its actual implementation.

Do not guess:

-   payload property names
-   response property names
-   status codes
-   query parameters
-   ID types
-   error structure

If frontend and backend disagree:

**fix the contract intentionally rather than adding ad-hoc frontend
transformations everywhere.**

------------------------------------------------------------------------

# 56. Required Security Testing

Test frontend integration using multiple roles.

At minimum:

-   Leadership
-   Admin
-   Sales Executive
-   Sales Manager
-   Pre-Sales Manager
-   Solution Engineer
-   Delivery Manager
-   DevOps Engineer
-   Data Analyst

Test:

-   active-role isolation
-   unauthorized routes
-   unauthorized API calls
-   closed opportunity
-   OEM redaction
-   Deal Finder immutability
-   Decision Maker constraint
-   POC team limit
-   value mutation permissions
-   lifecycle permissions

------------------------------------------------------------------------

# 57. Required End-to-End Flow

The frontend must support the complete valid business flow:

``` text
Lead
 ↓
Submit
 ↓
Sales Manager Review
 ↓
Approve
 ↓
Qualified
 ↓
RFX
 ↓
Drive Link
 ↓
POC
 ↓
POC Request
 ↓
Delivery Manager
 ↓
POC Team
 ↓
POC Execution
 ↓
POC Result
 ↓
Negotiations
 ↓
PSM / Leadership approval
 ↓
Closed Won
 ↓
Delivery Project
 ↓
Delivery completion
```

Also test:

``` text
Lead
 ↓
Close Lost
 ↓
Closed
 ↓
Locked
```

------------------------------------------------------------------------

# 58. Database Verification Checklist

Before declaring frontend complete:

-   [ ] current Alembic head inspected
-   [ ] all required tables exist
-   [ ] all required relationships exist
-   [ ] required indexes exist
-   [ ] Decision Maker constraint works
-   [ ] account uniqueness works
-   [ ] POC member limit works
-   [ ] historical records are protected
-   [ ] migrations run cleanly
-   [ ] clean DB can be created
-   [ ] existing DB can be upgraded
-   [ ] seed/reset works
-   [ ] no manual-only schema modifications remain

------------------------------------------------------------------------

# 59. Final Deliverables

The teammate/agent should deliver:

``` text
frontend implementation
backend fixes required for frontend integration
database migrations required for backend fixes
updated tests
updated seed data if required
API documentation updates
frontend documentation
integration report
```

At minimum, create/update:

``` text
FRONTEND_IMPLEMENTATION_REPORT.md
FRONTEND_API_INTEGRATION.md
FRONTEND_DATABASE_CHANGES.md
FRONTEND_TEST_REPORT.md
```

------------------------------------------------------------------------

# 60. Final Certification

Before completion, report:

``` text
FRONTEND STATUS

Authentication: PASS/FAIL
Active Role: PASS/FAIL
Navigation: PASS/FAIL
Dashboards: PASS/FAIL
Search: PASS/FAIL
Opportunities: PASS/FAIL
Accounts: PASS/FAIL
Stakeholders: PASS/FAIL
OEM: PASS/FAIL
RFX: PASS/FAIL
POC: PASS/FAIL
Negotiations: PASS/FAIL
Delivery: PASS/FAIL
Activities: PASS/FAIL
Follow-ups: PASS/FAIL
Notifications: PASS/FAIL
Audit/History: PASS/FAIL
Revenue: PASS/FAIL
Concurrency: PASS/FAIL
Error Handling: PASS/FAIL
Security: PASS/FAIL

Database:
Migrations: PASS/FAIL
Constraints: PASS/FAIL
Indexes: PASS/FAIL
Seed/Reset: PASS/FAIL

Backend:
Regression Tests: PASS/FAIL

Frontend:
Production Build: PASS/FAIL
```

Then report:

## Implemented

What was actually completed.

## Backend Changes

What backend code was changed for frontend integration.

## Database Changes

Every migration/table/index/constraint added or changed.

## Bugs Fixed

Existing backend/frontend bugs discovered during integration.

## Security Findings

Any authorization/data exposure issues discovered.

## Remaining Gaps

Anything not completed.

## Decisions Required

Anything that cannot safely be inferred.

------------------------------------------------------------------------

# 61. Most Important Instruction

**Do not treat this as "just frontend".**

The objective is:

``` text
ONE COHERENT FULL-STACK DEAL ROOM SYSTEM
```

If the frontend exposes a missing backend capability, fix the backend.

If the backend requires persistence that the database does not support,
change the database through Alembic.

If the database change requires API changes, update the API.

If the API changes, update the frontend.

Then test the entire chain.

The correct dependency is:

``` text
Business requirement
        ↓
Database model
        ↓
Backend authorization/service
        ↓
API contract
        ↓
Frontend state/API client
        ↓
UI
        ↓
End-to-end test
```

Never reverse this by creating fake frontend state and pretending the
backend supports it.

------------------------------------------------------------------------

# 62. Final Non-Regression Rule

Everything implemented in Phase 1, Phase 2 and Phase 3 remains frozen
unless an explicit requirement requires a change.

Do not regress:

-   lifecycle
-   roles
-   active-role isolation
-   Deal Finder
-   authorization
-   revenue rules
-   closed-record lock
-   account rules
-   stakeholder rules
-   OEM redaction
-   RFX → POC requirement
-   POC rules
-   Negotiations gate
-   Delivery Project
-   activities
-   follow-ups
-   notifications
-   audit/history
-   concurrency
-   database integrity

The frontend is considered complete only when it correctly represents
and interacts with these backend rules.
