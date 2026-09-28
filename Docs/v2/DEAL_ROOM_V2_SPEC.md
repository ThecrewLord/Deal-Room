# Deal Room v2 Specification

**Status:** FROZEN --- Phase 2\
**Purpose:** Single source of truth for the new Deal Room v2
requirements.

## 1. Product

Deal Room is an internal commercial-operations platform for
opportunities, stakeholders, technical POCs, delivery handoff,
centralized accounts, OEM partners, lightweight activity/status
information, notifications, audit history, and pipeline reporting.

Architecture remains React/Vite -\> Flask REST API -\>
PostgreSQL/SQLAlchemy. The backend is authoritative for validation,
workflow, authorization, audit, and concurrency.

## 2. Roles

### Leadership

Root privileged role. Has company-wide business visibility and system
governance, including deciding who is Admin.

The first system user is Leadership. The system must never permit the
last Leadership account to be removed or demoted.

### Admin

Delegated system administrator. Admin manages access only within
privileges delegated by Leadership.

Admin cannot: - create leads - view business pipeline - see other
Admins - grant Admin or Leadership - grant themselves another role -
close opportunities - change business opportunity data

### Business hierarchy

-   Sales Manager -\> Sales Executive
-   Pre-Sales Manager -\> Solution Engineer
-   Delivery Manager -\> DevOps Engineer / Data Analyst

## 3. Active role

Users may have multiple roles, but one active role governs a session.
Permissions are never combined across roles. Backend validation is
mandatory; frontend role state is not a security boundary.

## 4. Deal Finder and participation

The Deal Finder is the person who creates/founds the lead and is
immutable forever.

Deal Finder is separate from Sales Executive participation.

Opportunity UI should identify participants by title: - Deal Finder -
Sales Executive - Solution Engineer(s) - Delivery member(s)

Historical participation must remain auditable.

## 5. Central Accounts

Accounts are centralized and visible to employees only for canonical
company-identification purposes.

Employees can search and add accounts. The Accounts page is a row/list
view and is not a route into opportunity data.

Opportunity creation selects an existing canonical account; there is no
inline "create account" flow.

Duplicate prevention is mandatory and must include archived accounts.

Leadership can archive accounts. Archiving is preferred to physical
deletion so historical references survive. An account with no
opportunity may still be archived.

## 6. Opportunity creation

The authorized Deal Finder creates a Lead.

Required at creation: - canonical account - required opportunity
fields - initial opportunity value

Before submission to Sales Manager: - description is mandatory - at
least one stakeholder is mandatory - pain points are mandatory

The opportunity appears at Lead.

## 7. Initial Sales Manager workflow

Deal Finder submits the Lead.

Sales Manager has exactly three actions:

### Approve

Sales Manager may edit permitted opportunity details and must assign a
Sales Executive. Approval automatically moves the opportunity to
Qualified.

### Closed Won

May be done immediately without assigning a Sales Executive.

### Closed Lost

May be done immediately without assigning a Sales Executive. Closed Lost
reason rules apply.

Sales Executive assignment is therefore mandatory for
continuation/approval, not for immediate closure.

After Qualified, Sales Executive and Sales Manager lose stage-edit
authority.

## 8. Lifecycle

Normal lifecycle:

`Lead -> Qualified -> RFX -> POC -> Negotiations -> Delivery`

No stage skipping.

`POC -> RFX` reopening is future scope.

Closed Won and Closed Lost are terminal outcomes, not ordinary forward
lifecycle stages.

## 9. Post-Qualified editing

After Qualified: - Solution Engineer may update description - Pre-Sales
Manager may update description - Leadership may update description -
Sales Executive cannot edit ordinary opportunity fields - Sales
Executive can add/manage stakeholders only as explicitly authorized

Stage changes after Qualified are limited to Pre-Sales Manager,
authorized Solution Engineer(s), and Leadership.

## 10. RFX

Solution Engineer can progress an authorized opportunity to RFX.

The required RFX Google Drive link is used for POC documentation. Deal
Room must not claim to verify Drive permissions without real Drive
integration.

## 11. POC

POC is the lifecycle stage and supports multiple POC records.

A POC request requires: - success metrics - exit criteria - input Google
Drive link - edit-access guidance/disclaimer

Delivery Manager receives the assignment task and can assign up to two
people: - DevOps Engineer - Data Analyst - or both

Delivery members can see authorized opportunity/POC information and the
supplied Drive link, perform the POC externally, upload demo/results
externally, and submit a view link.

POC submission notifies the Solution Engineer.

Multiple POCs are retained as history. Submitted POC results are
immutable. No POC deletion in normal workflow.

## 12. Negotiations

Negotiations is mandatory between POC and Delivery.

NDA, MSA, SOW, etc. may be handled here. No document is mandatory solely
to enter Negotiations. NDA is a suggestion, not a required field.

## 13. Negotiations -\> Delivery

Normal completion requires Pre-Sales Manager approval.

At the final gate, Pre-Sales Manager can: - Approve Closed Won -\>
Delivery - Close Lost -\> Closed Lost

Sales Manager does not perform this final approval.

After approval, the opportunity becomes available to the Delivery
Manager.

## 14. Closure

### Before Qualified / initial review

Sales Manager and Leadership may close Won/Lost.

### Qualified onward

Pre-Sales Manager and Leadership may close Won/Lost. Solution Engineer
may close Lost and may request Closed Won, but Closed Won requires
Pre-Sales Manager approval. Sales Executive, Delivery roles, and Admin
cannot close.

Closed Lost: - standard reason mandatory - explanation optional -
explanation mandatory when standard reason = Other

Closed opportunities are locked. Leadership is the only role reserved
for future reopen authority.

## 15. Delivery

Delivery Manager receives projects after the final Pre-Sales Manager
Closed Won approval.

The POC team is preselected as the suggested Delivery team; the Delivery
Manager can change it.

Delivery employees may mark their own work Done, but Delivery Manager
can mark the project Done regardless of employee Done status.

## 16. OEM partners

An opportunity may have multiple OEM partners.

Employees can see OEM names attached to authorized opportunities.

Only Leadership can CRUD the OEM master data. Employees do not see OEM
contact-person details. OEM contact management is outside v2.

## 17. Stakeholders

Fields: - name - job title - email - phone - company - tags

Tags: - Economic Buyer - Technical Champion - End User - Blocker -
Decision Maker

Stakeholders may have multiple tags. Only one Decision Maker may exist
per opportunity. This must be enforced transactionally/server-side.

## 18. Opportunity value and revenue

At creation, Deal Finder sets the initial Opportunity Value.

After creation, current Opportunity Value may be changed by: - Sales
Manager - Pre-Sales Manager - Leadership

Every value change requires: - old value - new value - reason - actor -
timestamp

A complete value history is retained.

At Closed Won:

`Final Revenue = current Opportunity Value at closing`

Final Revenue is immutable for normal users and auditable.

There is no incentive calculation in v2.

## 19. Revenue reporting

Sales Executives can see revenue generated by closed-won opportunities
where they are the Deal Finder, subject to their visibility.

Sales Managers can see, per Sales Executive: 1. **Sourced Revenue:**
closed-won revenue where that Sales Executive is the immutable Deal
Finder. 2. **Participation Revenue:** closed-won revenue from all
opportunities in which that Sales Executive participated.

Leadership can see company-wide performance.

Historical reporting must not disappear because a user's current
manager/role changes.

## 20. Operational status

Status is: - Active - Stalled - Closed

Stage and status are separate.

Closed Won/Lost imply Closed status.

## 21. Activity/follow-up scope

Keep the existing lightweight activity/follow-up capability where it is
already implemented, but do not introduce a complex activity-state
model. The opportunity's high-level operational status remains
Active/Stalled/Closed.

## 22. Events and notifications

Use one event model:

`Business action -> domain event -> audit -> notification`

Examples: - Lead submitted -\> Sales Manager - approval/assignment -\>
downstream participant - POC request -\> Delivery Manager - POC result
-\> Solution Engineer - Closed Won request -\> Pre-Sales Manager - final
approval -\> Delivery Manager

No duplicate notification architecture.

## 23. Audit/history

Meaningful business changes must be retained: - Deal Finder - stage -
approvals/rejections - opportunity value - assignments - description -
pain points where changed - stakeholders/tags - POC requests/results -
Delivery assignment/completion - closure - Closed Lost reason - account
archival - OEM changes - access/role changes

History must never be silently rewritten.

## 24. Concurrency

Optimistic concurrency remains required. Sensitive mutations validate
the version/updated timestamp and fail safely on stale writes.

## 25. Google Drive boundary

Deal Room stores links and permission guidance. It does not verify
Google Drive view/edit permissions unless a real Drive integration is
implemented.

## 26. Explicit non-goals

Not in v2: - POC -\> RFX reopening - stage skipping - incentive
calculations - OEM contact management - full project management - Google
Drive permission verification - generic unrestricted CRUD - Admin
business access - Sales Executive closure - normal POC deletion - inline
account creation

## 27. Frozen invariants

1.  Deal Finder never changes through normal application operations.
2.  Last Leadership cannot be removed/demoted.
3.  Admin cannot create leads or access business pipeline.
4.  Sales Executive cannot close.
5.  Closed opportunities are locked.
6.  Only authorized technical roles change post-Qualified stage.
7.  Stage skipping is forbidden.
8.  POC -\> RFX is future scope.
9.  One Decision Maker per opportunity.
10. Value changes require reason/history.
11. Final Revenue equals value at Closed Won.
12. Closed Lost requires standard reason.
13. Other requires explanation.
14. Multiple OEMs per opportunity are supported.
15. Delivery Manager can complete a project without employee Done
    clicks.
16. No incentive domain exists in v2.
