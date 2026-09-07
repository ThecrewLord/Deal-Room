# Deal Room v2 Gap Analysis

**Baseline:** Latest Phase 10-era Deal Room implementation artifacts
available in the project context/file library, plus the subsequently
frozen v2 decisions.\
**Confidence:** Architectural gap analysis. The latest runnable ZIP was
not directly executable in this turn, so exact runtime behavior is
marked as needing verification rather than being claimed as proven.

## 1. Classification

-   KEEP = architecture/concept remains correct.
-   MODIFY = useful existing component, but rules/data/permissions must
    change.
-   REPLACE = materially conflicts with v2.
-   DELETE = obsolete in v2.
-   NEW = capability required by v2 but not adequately represented.

## 2. Executive summary

The existing architecture should not be thrown away. It already has
React/Vite, Flask REST, PostgreSQL/SQLAlchemy, centralized
AuthorizationService, OpportunityService, PocService,
SolutionDesignService, ActivityService, NotificationService, AuditLog,
OpportunityTeam, StageMaster and StageHistory concepts. The project
instructions explicitly required preserving these services and avoiding
duplicate authorization/notification/audit architectures.

The major v2 conflicts are ownership semantics, roles, lifecycle names,
closure authority, value/revenue modeling, stakeholder tags, OEM
visibility, delivery hierarchy, and generic mutation paths.

The seed implementation is particularly important: current code sets
`created_by` and `sales_owner_id` to a Sales Executive, which conflicts
with the new immutable Deal Finder + separate participation model.

## 3. Architecture

  ------------------------------------------------------------------------
  Component               Classification          Action
  ----------------------- ----------------------- ------------------------
  Flask app factory       KEEP                    Preserve

  SQLAlchemy              KEEP                    Preserve

  PostgreSQL              KEEP                    Preserve

  Flask-Migrate/Alembic   KEEP                    Preserve

  AuthorizationService    MODIFY                  Add relationship +
                                                  stage + field-level
                                                  rules

  AuthService             MODIFY                  Add Leadership/root
                                                  invariants and new roles

  OpportunityService      MODIFY                  Become authoritative
                                                  workflow/value/closure
                                                  service

  PocService              MODIFY                  Repeatable POCs and v2
                                                  permissions

  SolutionDesignService   MODIFY                  Align to
                                                  RFX/POC/Negotiations

  ActivityService         KEEP/MODIFY             Keep lightweight
                                                  activity scope

  NotificationService     KEEP/MODIFY             One event-driven path

  Audit infrastructure    KEEP/MODIFY             Expand history/event
                                                  coverage

  Generic CRUD mutation   REPLACE                 Explicit workflow
                                                  actions

  Search                  KEEP/MODIFY             Reuse authorized query
                                                  scopes

  Dashboard               MODIFY                  Leadership and
                                                  sourced/participation
                                                  revenue
  ------------------------------------------------------------------------

The Phase 10 requirements explicitly say search must use the same
server-side authorization scope as list/detail access and must not
become a second authorization system.

## 4. Roles

Current six-role implementation: - Admin - Sales Executive - Sales
Manager - Pre-Sales Manager - Solution Engineer - Delivery

V2: - Leadership - Admin - Sales Manager - Sales Executive - Pre-Sales
Manager - Solution Engineer - Delivery Manager - DevOps Engineer - Data
Analyst

  Existing component   Classification
  -------------------- ----------------
  User                 MODIFY
  UserRole             MODIFY
  Active role/JWT      MODIFY
  Admin workflow       MODIFY
  Manager hierarchy    MODIFY
  Leadership           NEW
  Delivery Manager     NEW
  DevOps Engineer      NEW
  Data Analyst         NEW
  Multi-role tests     MODIFY

## 5. Opportunity ownership

Existing implementation has `created_by`, `sales_owner_id`, and
OpportunityTeam. Earlier phases correctly recognized creator and Sales
Owner as separate concepts.

However, current seed code explicitly assigns both `created_by` and
`sales_owner_id` to a Sales Executive. That is incompatible with v2
where the Deal Finder can be a non-Sales employee and where Deal Finder
must remain immutable.

  Component                               Classification
  --------------------------------------- -------------------
  `created_by` concept                    MODIFY
  `sales_owner_id` as primary ownership   REPLACE/DEPRECATE
  OpportunityTeam                         MODIFY
  Immutable Deal Finder                   NEW
  Participant/title representation        NEW/MODIFY
  Assignment history                      MODIFY

Do not destroy historical fields blindly; migrate semantic use first.

## 6. Lifecycle

Existing seed/history artifacts contain older stage names such as
Discovery, POC / Technical Evaluation, Proposal and Negotiation.

V2: `Lead -> Qualified -> RFX -> POC -> Negotiations -> Delivery`

  Component                         Classification
  --------------------------------- -----------------------------------------------
  StageMaster                       MODIFY
  StageHistory                      KEEP/MODIFY
  Stage constants                   REPLACE
  Discovery                         DELETE from active workflow; preserve history
  Proposal                          DELETE from active workflow; preserve history
  POC / Technical Evaluation name   REPLACE with POC
  Closed Won/Lost stage treatment   MODIFY
  Explicit transition validator     MODIFY/NEW
  POC -\> RFX                       DELETE from current transitions

Historical stage records must not be destroyed merely because the active
workflow changed.

## 7. Opportunity fields

Current seed evidence includes account_id, opportunity_name, stage_id,
estimated_value, probability, expected_close_date, timestamps, status,
is_active, created_by and sales_owner_id.

V2 additionally/changes: - immutable Deal Finder - description - pain
points - current Opportunity Value - Final Revenue - Value History -
Closed Lost reason/explanation - multiple OEM relationship - participant
assignments

  Field/concept                Classification
  ---------------------------- ---------------------------------
  account_id                   KEEP
  opportunity_name             KEEP
  stage_id                     MODIFY
  status                       MODIFY
  is_active                    MODIFY/deprecate if redundant
  created_by                   MODIFY semantics
  sales_owner_id               REPLACE/deprecate
  description                  MODIFY/NEW
  pain_points                  NEW
  estimated_value              MODIFY into current value model
  final revenue                NEW
  value history                NEW
  lost reason                  NEW/MODIFY
  lost explanation             NEW
  generic opportunity DELETE   DELETE

Probability/forecasting is not part of the frozen v2 requirements and
should be reviewed before being retained as a business-critical field.

## 8. Revenue

Current implementation uses an estimated/forecast value model. V2 needs:

`Current Opportunity Value + Value History + Final Revenue`

  Component                      Classification
  ------------------------------ ----------------
  estimated/forecast value       MODIFY
  current value                  MODIFY
  value history                  NEW
  final revenue                  NEW
  incentive calculation          DELETE
  incentive rate                 DELETE
  incentive attribution          DELETE
  sourced revenue report         NEW
  participation revenue report   NEW

No incentive domain should remain half-functional.

## 9. Stakeholders

Current seed stakeholder fields include name, designation, email, phone,
influence_level and notes. Current test data also uses older labels such
as Decision Maker, Influencer and User.

V2: - name - job title - email - phone - company - multiple tags - one
Decision Maker

  Component                   Classification
  --------------------------- ----------------
  Stakeholder                 MODIFY
  designation -\> job title   MODIFY
  influence_level             REPLACE
  Tag model                   KEEP/MODIFY
  stakeholder-tag relation    NEW/MODIFY
  Decision Maker uniqueness   NEW
  Stakeholder authorization   MODIFY

## 10. Accounts

Existing Account/Contact models and account_id relationships are useful.

V2: - centralized account directory - duplicate prevention - no inline
account creation during opportunity creation - employee-safe canonical
details - Leadership archive

  Component                              Classification
  -------------------------------------- ----------------
  Account                                MODIFY
  Contact                                REVIEW/MODIFY
  Account authorization                  MODIFY
  Duplicate detection                    NEW
  Archive                                NEW/MODIFY
  Account -\> opportunity visibility     REPLACE
  Inline account creation                DELETE
  Contact derivation from stakeholders   REVIEW

Archive rather than physically delete where historical references exist.

## 11. OEM

Existing OEMPartner already exists, but seed data currently includes
partner contact person and email fields.

V2: - many OEMs per opportunity - employee sees OEM name only -
Leadership CRUD - no OEM contact management

  Component                         Classification
  --------------------------------- ----------------
  OEMPartner                        MODIFY
  OEM master registry               KEEP/MODIFY
  Opportunity-OEM relationship      NEW/MODIFY
  Employee OEM contact visibility   DELETE
  OEM contact UI                    DELETE
  Leadership OEM CRUD               MODIFY

Existing contact columns may be retained for historical compatibility,
but must not be exposed to employees.

## 12. POC

Existing project already has Poc, POCTracker and PocService, and earlier
Phase 6 requirements intentionally made POCs historical/auditable and
allowed multiple POCs.

  Component                  Classification
  -------------------------- ----------------
  Poc                        KEEP/MODIFY
  POCTracker                 MODIFY
  PocService                 MODIFY
  Multiple POCs              KEEP
  POC deletion               DELETE
  Submitted-result editing   DELETE
  POC -\> RFX                DELETE
  Delivery assignment        MODIFY
  Drive links                MODIFY

## 13. Delivery

Old implementation has a generic Delivery role. V2 changes this to a
hierarchy:

Delivery Manager -\> DevOps Engineer / Data Analyst

  Component                     Classification
  ----------------------------- ----------------
  Old Delivery role             REPLACE
  Delivery Manager              NEW
  DevOps Engineer               NEW
  Data Analyst                  NEW
  Delivery assignment           MODIFY
  POC-team default suggestion   NEW
  Delivery completion           NEW/MODIFY

Do not simply rename old Delivery to Delivery Manager; the permissions
are different.

## 14. Status

Existing implementation uses OPEN/CLOSED and `is_active`.

V2: `Active | Stalled | Closed`

  Component                  Classification
  -------------------------- -------------------------------
  status                     MODIFY
  is_active                  MODIFY/deprecate if redundant
  stalled state              NEW/MODIFY
  stage/outcome separation   MODIFY

Avoid two fields that can contradict each other.

## 15. Closure

Earlier implementation allowed Solution Engineer closure and used old
stage names. V2 changes: - Sales Executive can never close - Sales
Manager closes directly only during initial Lead review - Pre-Sales
Manager closes after Qualified - Leadership closes at permitted stages -
SE Closed Won requires Pre-Sales Manager approval - final Negotiations
gate is Pre-Sales Manager -\> Delivery

  Component                     Classification
  ----------------------------- ----------------
  Close Won endpoint concept    KEEP/MODIFY
  Close Lost endpoint concept   KEEP/MODIFY
  Generic stage_id closure      DELETE
  Closure authorization         MODIFY
  Closure approval workflow     MODIFY
  Closed-state locking          KEEP/MODIFY

## 16. Audit

AuditLog already exists and audit was a core Phase 10 pillar.

  Area                         Classification
  ---------------------------- ----------------
  AuditLog                     KEEP
  Audit service                KEEP/MODIFY
  Stage history                KEEP/MODIFY
  Value history                NEW
  Deal Finder history          NEW
  Closure history              MODIFY
  Assignment history           MODIFY
  POC history                  KEEP/MODIFY
  Leadership override events   NEW
  Account archive events       NEW
  OEM events                   NEW
  Stakeholder tag events       NEW

## 17. Notifications

Notification and NotificationService already exist.

  Component                             Classification
  ------------------------------------- ----------------
  Notification model                    KEEP/MODIFY
  NotificationService                   KEEP/MODIFY
  Domain-event mapping                  MODIFY
  Duplicate/ad-hoc notification paths   DELETE/REPLACE

## 18. Search

Keep the architecture, but ensure:
`authorized query -> search filter -> results`

Never: `fetch everything -> frontend filter`

## 19. Generic CRUD

Earlier Phase 6 requirements explicitly warned that generic POC
PUT/DELETE could bypass workflow.

  Pattern                                Classification
  -------------------------------------- ----------------
  Explicit workflow actions              KEEP
  Generic unrestricted opportunity PUT   REPLACE
  Generic unrestricted POC PUT           REPLACE
  Generic POC DELETE                     DELETE
  Generic stage_id mutation              DELETE
  Close via arbitrary field edit         DELETE

## 20. Frontend

  Component                                     Classification
  --------------------------------------------- ----------------
  React/Vite foundation                         KEEP
  Shared theme/components                       KEEP
  Opportunity detail                            MODIFY
  Old owner UI                                  REPLACE
  Opportunity creation                          MODIFY
  Stakeholder UI                                MODIFY
  POC UI                                        MODIFY
  Leadership dashboard                          NEW/MODIFY
  Sales Manager sourced/participation revenue   NEW
  Delivery Manager Pending Assignment           NEW
  Delivery Projects                             NEW/MODIFY
  Admin business dashboard                      DELETE/REPLACE
  Frontend-only permissions                     DELETE

## 21. Seed data

The seed architecture is idempotent and non-destructive; preserve that.

Current seed scripts import Accounts, Opportunities, Stakeholders, POC
Tracker, Activity Log and OEM Partners and already use centralized
role/stage constants. However, current seed assumptions are incompatible
with v2 in several places.

  Seed area                          Classification
  ---------------------------------- ----------------
  Idempotent seed approach           KEEP
  Canonical role constants           MODIFY
  Six-role identities                MODIFY
  Leadership                         NEW
  Delivery Manager/DevOps/Data       NEW
  Deal Finder diversity              MODIFY
  Creator = Sales Exec               DELETE
  Creator = Sales Owner assumption   DELETE
  Old stage names                    REPLACE
  Old stakeholder tags               REPLACE
  OEM contact exposure               DELETE
  Revenue history                    NEW
  Closed Lost reasons                NEW
  Multiple OEM links                 NEW

## 22. Database constraints to add

1.  One Decision Maker per Opportunity.
2.  Deal Finder required after Lead creation.
3.  Deal Finder immutable through normal mutation.
4.  Value history references valid opportunity/actor.
5.  Final Revenue cannot be changed through normal updates.
6.  Closed Lost reason required.
7.  Other requires explanation.
8.  POC active assignment \<= 2.
9.  Explicit stage transition rules.
10. Last Leadership cannot be removed/demoted.
11. Archived Accounts remain valid historical references.
12. Duplicate Account creation is blocked/warned through canonical
    matching.
13. Multiple OEM links supported without duplicate links.
14. Historical audit records cannot be deleted normally.

## 23. Highest-risk security gaps

### Critical

1.  Frontend-only authorization.
2.  Generic PUT capable of changing stage/Deal Finder/value/assignment.
3.  Active-role permission combination.
4.  Admin business-data leakage.
5.  Silent historical mutation.

### High

6.  Account directory becoming an opportunity backdoor.
7.  Value manipulation without immutable history.
8.  Two concurrent Decision Makers.
9.  POC assignment exceeding two members under concurrent writes.
10. Concurrent closure based on stale state.
11. OEM contact leakage through existing serializers.
12. Old role/stage constants still accepted by backend.

## 24. Recommended implementation order

1.  Roles + Leadership invariants.
2.  Lifecycle constants and transition validator.
3.  Deal Finder/participant model.
4.  Opportunity value/history/final revenue.
5.  Authorization redesign.
6.  Account duplicate prevention/archive.
7.  Stakeholder tags + Decision Maker constraint.
8.  OEM many-to-many + visibility.
9.  Sales Manager Lead workflow.
10. RFX/POC workflow.
11. Delivery Manager hierarchy/workflow.
12. Negotiations final Pre-Sales approval.
13. Closure/locking.
14. Revenue reporting.
15. Event/notification/audit alignment.
16. Frontend.
17. Seed data.
18. Direct API security tests.
19. Concurrency/regression testing.

## 25. Final classification summary

### KEEP

-   Flask
-   React/Vite
-   PostgreSQL
-   SQLAlchemy
-   migrations
-   centralized authorization architecture
-   AuthService
-   NotificationService
-   Audit infrastructure
-   OpportunityService concept
-   PocService concept
-   SolutionDesignService concept
-   StageHistory
-   multiple POCs
-   optimistic concurrency
-   non-destructive seed philosophy

### MODIFY

-   roles
-   active role
-   AuthorizationService
-   Opportunity
-   OpportunityTeam
-   StageMaster
-   StageHistory
-   Account
-   Stakeholder
-   Tag
-   OEMPartner
-   POC/POCTracker
-   dashboards
-   notifications
-   audit
-   search
-   seed data
-   frontend

### REPLACE

-   sales_owner_id as primary ownership model
-   old lifecycle transitions
-   generic unrestricted mutation
-   old stakeholder influence/tag semantics
-   old Delivery role semantics

### DELETE

-   incentive domain
-   Sales Executive closure
-   POC -\> RFX transition
-   stage skipping
-   generic POC DELETE
-   generic stage mutation
-   inline account creation
-   employee OEM contact visibility
-   Admin business pipeline access
-   obsolete old role/stage UI

### NEW

-   Leadership
-   Delivery Manager
-   DevOps Engineer
-   Data Analyst
-   immutable Deal Finder
-   participant/title model
-   pain points
-   value history
-   final revenue
-   sourced revenue
-   participation revenue
-   account duplicate prevention
-   account archive
-   multi-tag stakeholder relation
-   Decision Maker constraint
-   multi-OEM opportunity relationship
-   POC-derived delivery suggestion
-   final Pre-Sales approval gate
-   Delivery completion
-   v2 security invariants/tests
