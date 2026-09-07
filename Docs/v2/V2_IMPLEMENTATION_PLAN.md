# Deal Room v2 Implementation Plan

**Precondition:** resolve the sole remaining Deal Finder eligibility item in [V2_DECISIONS_REQUIRED.md](V2_DECISIONS_REQUIRED.md), approve the state model, and take a PostgreSQL schema/data backup. This plan deliberately evolves the existing service architecture identified in [V2_IMPLEMENTATION_AUDIT.md](V2_IMPLEMENTATION_AUDIT.md); it does not create a second authorization, notification, or audit system.

## Cross-phase engineering rules

- Add migrations only through Alembic; inspect production data and execute data-validation queries before each constraint/backfill migration.
- Sensitive actions use explicit endpoint verbs, transaction boundaries, an expected integer version, authorization against the server-loaded state, audit, and notifications where required.
- Preserve legacy stage/ownership records and append history. Do not overwrite audit rows or submitted POC/value records.
- Establish `create_app(test_config=None)` (or equivalent config injection) before relying on the test suite; current import-time config prevents fixtures from selecting SQLite.
- Each phase is independently deployable only after its migration, backfill validation, API tests, and rollback plan are exercised in a non-production copy.

## Phase 0 — Foundation and migration preparation (required gate)

| Item | Plan |
|---|---|
| Files affected | `backend/app/config/config.py`, `backend/app/__init__.py`, test fixtures in `backend/tests/*.py`, `backend/migrations/env.py`, operational runbook under `Docs/v2/` |
| DB changes | None initially. Inventory live schema/head revision and both `poc`/`poc_tracker` tables; export counts, FK violations, stage/role distributions, duplicate accounts, and potential Decision Maker conflicts. |
| Migration required? | No, except a later migration baseline only after inventory. |
| API/auth/frontend | No product API change. Make test config injectable and fail securely when non-local secrets are absent. |
| Tests | Test app can start against a fresh SQLite/Postgres test database; migration upgrade/downgrade smoke test; baseline authorization snapshot tests. |
| Risks | Import-time `.env` behavior currently directs isolated tests to development PostgreSQL; never test against a shared database. |
| Rollback | Config/test-only changes are reversible. Backups and inventory reports are prerequisites for all irreversible data decisions. |

## Phase 1 — Authorization, Leadership, and roles

| Item | Plan |
|---|---|
| Files affected | `constants/roles.py`, `constants/organizations.py`, `models/auth/user.py`, `models/auth/user_role.py`, `services/auth_service.py`, `auth/authorization.py`, auth schemas/routes/controllers, frontend `auth/roles.js`, navigation, admin pages, migrations, tests. |
| DB changes | Add `Leadership`, `Delivery Manager`, `DevOps Engineer`, `Data Analyst` role values through data migration; add a delegated-admin permission representation only if D1/administration policy needs it. Do not use a Boolean `is_leadership`. |
| Migration required? | Yes: idempotent role vocabulary/backfill migration with preflight report for legacy Delivery -> new role mapping. Legacy Delivery cannot be blindly mapped because v2 splits it. |
| API changes | Leadership-only role/governance endpoints; Admin endpoints scoped by delegated privilege. Existing role-selection JWT flow stays, but active role validation recognizes all v2 roles. |
| Authorization | Extend existing `AuthorizationService.current_context`; add Leadership root scope and Admin self-escalation/other-Admin prohibitions. Transactionally prevent demotion/revocation/deletion of the last active Leadership. Preserve active-role—not union—semantics. |
| Frontend | Add role selection/navigation/pages only after server rules exist; Admin UI must hide other Admin identities and controls the server would deny. |
| Tests | Last Leadership race tests; active-role combinations; Admin cannot grant self/Admin/Leadership, view other Admins, or business data; Leadership company visibility; hierarchy validations. |
| Risks | Bulk role replacement can accidentally remove the final Leadership or invalidate sessions. Increment `auth_version` in the same transaction. |
| Rollback | Downgrade only maps newly introduced roles if no dependent v2 records exist; otherwise forward-fix with preserved `user_roles` history/audit. |

## Phase 2 — Lifecycle and transition engine

| Item | Plan |
|---|---|
| Files affected | `constants/stages.py`, `models/opportunity/stage_master.py`, `models/opportunity/opportunity.py`, `services/stage_service.py`, `services/opportunity_service.py`, opportunity schemas/routes/controllers, migration and tests. |
| DB changes | Add explicit lifecycle stage, outcome (`Open/Closed Won/Closed Lost`), operational status (`Active/Stalled/Closed`), lost reason/explanation, and integer `row_version`. Closed Won is terminal for the opportunity and creates a separate Delivery Project; preserve current `stage_id`, status, is_active as compatibility/read-only columns during cutover; do not rename historic stage rows in place. |
| Migration required? | Yes: create/backfill v2 stage data/mapping and validate every live legacy record. Decide D1/D2 before defining Delivery/Closed Won representation. |
| API changes | Replace arbitrary target-stage semantics with action endpoints: submit Lead, approve Lead, reject Lead, advance to RFX/POC/Negotiations, request/approve Closed Won, close Lost, mark stalled/active. Require expected version. |
| Authorization | Centralize matrix rules in `AuthorizationService` or a policy helper owned by it; reject stage skipping, POC->RFX, closed transitions, Admin/SE/Delivery stage mutations. |
| Frontend | Do not expose generic stage dropdown. Render allowed server-provided actions/status only. |
| Tests | Complete transition matrix; every forbidden edge; stale write; closed lock; self-review if approved in D4; audit history and atomic rollback on notification/audit failure. |
| Risks | Existing reports depend on `stage_id`, `status`, `is_active`, and `display_order`; run dual-read compatibility until report migration. |
| Rollback | Keep legacy fields/stages; only switch API reads after migration validation. Never delete historical stage rows in this phase. |

## Phase 3 — Deal Finder and participant model

| Item | Plan |
|---|---|
| Files affected | `models/opportunity/opportunity.py`, `opportunity_team.py` or new participant model, `services/opportunity_service.py`, `auth/authorization.py`, schemas/routes, seeds, frontend detail/create pages, migration/tests. |
| DB changes | Add immutable `deal_finder_id`; add participant/history fields (`participant_type`, role, assigned_by, assigned_at, ended_at, version) or extend `OpportunityTeam` safely. Retain `created_by` and `sales_owner_id` as legacy fields until reporting/API cutover. |
| Migration required? | Yes: backfill deal finder from `created_by`, record backfill provenance, leave exceptions visible for remediation. |
| API changes | Explicit participant assign/end/reassign actions; no generic change of Deal Finder. Lead creation accepts no finder ID—the actor is recorded server-side. |
| Authorization | Every approved active non-Admin role may create a Lead/act as Deal Finder; manager/pre-sales/Leadership scope checks apply after creation. Ensure no actor can assign arbitrary user IDs without approved status/eligible role. |
| Frontend | Participant titles: Deal Finder, Sales Executive, Solution Engineer(s), Delivery member(s), with history read-only. |
| Tests | Finder immutable by direct API payload; different Finder/SE; historic membership retained; multi-role actor active-role behavior; concurrent participant assignment. |
| Risks | Reusing `sales_owner_id` as Deal Finder corrupts existing meaning. Do not do it. |
| Rollback | New columns/tables can be left dormant; legacy ownership stays intact until acceptance. |

## Phase 4 — Opportunity value, value history, and final revenue

| Item | Plan |
|---|---|
| Files affected | opportunity model/service/schema/controller, dashboard/report repositories, audit activity constants, migrations/tests, frontend detail/reports. |
| DB changes | Add `current_value`, `final_revenue`, and append-only `opportunity_value_history` (old/new, reason, actor, active role, occurred_at, action/version). Backfill current value from `estimated_value` with migration reason `legacy_backfill`; do not fabricate historical changes. |
| Migration required? | Yes. Check null/negative/scale data before constraints. |
| API changes | `POST /opportunities/:id/value-changes` requiring expected version and reason; no value field in generic update. Closed Won action snapshots final revenue in the same transaction. |
| Authorization | Creation actor sets initial value; only Sales Manager, Pre-Sales Manager, Leadership change afterwards; no changes after final revenue/closure. |
| Frontend | Value history timeline; authorized edit dialog with reason; reports show Sourced/Participation Revenue, no incentives. |
| Tests | Initial value required; values/history/audit exactness; stale concurrent updates; role denial; final revenue equals exact current value and is immutable. |
| Risks | Decimal rounding and old dashboards’ `estimated_value`/probability assumptions. Use fixed `Numeric` and dual-read reports during migration. |
| Rollback | Retain old value; value history is append-only. Do not downgrade by deleting legitimate records after production use. |

## Phase 5 — Central accounts, duplicate prevention, and archive

| Item | Plan |
|---|---|
| Files affected | account model/repository/service/controller/schema/routes, `AuthorizationService.account_query`, search service, opportunity create flow, frontend Accounts/Opportunities, audit/migration/tests. |
| DB changes | Add archive fields (`archived_at/by/reason`) and approved `canonical_name_key`; create unique index across active and archived records after collision cleanup. |
| Migration required? | Yes; D6 must define normalization and collision resolution first. |
| API changes | Dedicated employee directory list/search/detail DTO (no opportunity counts/links); account creation route; Leadership edit/archive/reactivate actions; opportunity create accepts an existing, non-archived account only. |
| Authorization | Every approved active non-Admin role can search/view/add central accounts; Admin denied; Leadership edit/archive/ban; eliminate account visibility derived from opportunities. Ensure account API never returns linked opportunity data. |
| Frontend | Standalone Accounts directory; remove inline account creation from `Opportunities.jsx`; create Account flow navigates/returns selection before lead creation. |
| Tests | Archived duplicates rejected/resolved; case/suffix normalization; unauthorized account data/archives; account does not disclose opportunity visibility; concurrent identical create. |
| Risks | False-positive normalization can block real companies. Provide Leadership resolution per D6. |
| Rollback | Archive is reversible; keep original names and mapping; avoid physical deletes. |

## Phase 6 — Stakeholder tags and Decision Maker constraint

| Item | Plan |
|---|---|
| Files affected | stakeholder/tag models/repositories/services/schemas/routes, authorization, audit constants, migration/tests, stakeholder UI. |
| DB changes | Add/rename job title/company fields; create controlled tag catalog and `stakeholder_tags` join. Enforce at most one Decision Maker per opportunity with PostgreSQL partial unique index (or a dedicated pointer plus transaction) and row-version columns. Retain legacy influence level until backfill acceptance. |
| Migration required? | Yes: map safe legacy labels; report conflicts rather than arbitrarily picking a Decision Maker. |
| API changes | Explicit create/update/tag-set action accepting expected stakeholder/opportunity version; no tag mutation hidden in generic payload. |
| Authorization | Encode exact matrix scope/stage rules after D9; deny all closed mutation; validate opportunity access server-side. |
| Frontend | Multi-select tags and a clear single Decision Maker indicator; use server conflict response, not UI-only validation. |
| Tests | Multiple tags; concurrent Decision Maker writes; reassignment in one transaction; unauthorized role/stage/closed state; audit tag diffs. |
| Risks | Partial index syntax and SQLite test parity; add Postgres integration coverage. |
| Rollback | Preserve mapped legacy influence values and tag history; forward-fix conflicts. |

## Phase 7 — OEM master, association, and visibility

| Item | Plan |
|---|---|
| Files affected | OEM model/repository/service/controller/schema/routes, opportunity DTOs, authorization, migration/tests, Leadership/OEM UI. |
| DB changes | Keep OEM master/contact fields under Leadership; add `opportunity_oem_partners` junction with association audit/version. Do not move master rows from account ownership until data mapping is approved. |
| Migration required? | Yes for junction; existing account links must be treated as legacy associations only after business review. |
| API changes | Leadership CRUD/archive master endpoints; explicit attach/detach existing master actions per D7; employee DTO returns name only on authorized opportunity. |
| Authorization | Leadership sees/changes contact details; Admin denied; employees never receive contact PII. Every approved active non-Admin Deal Finder may select existing OEMs while creating their opportunity; Sales Manager may do so during initial review; thereafter attachment scope follows D7. |
| Frontend | Leadership master registry; opportunity displays names only, no contact data; no employee contact-management UI. |
| Tests | PII serialization regression; multiple attachment; scope/role denial; closed association rules; audit and stale write. |
| Risks | Existing `GET /api/oem` leaks contacts now. Restrict DTO before expanding usage. |
| Rollback | Junction can be removed only before production associations; retain OEM master contacts/historical audit. |

## Phase 8 — v2 POC workflow

| Item | Plan |
|---|---|
| Files affected | `POCTracker` model/service/repository/schema/routes, authorization, notification/audit services, POC UI, migrations/tests; evaluate `models/poc/poc.py`. |
| DB changes | Add request input Drive link, access disclaimer acknowledgment, success/exit criteria, result view link, immutable submission snapshot, POC row version, and POC assignment relation limited to two active DevOps/Data members. Add explicit request/submitted timestamps/actors. |
| Migration required? | Yes. Inventory and decide the orphan `poc` table before consolidation; no destructive removal during initial v2 rollout. |
| API changes | Explicit request, assign/reassign, start/submit result, review, and create-next-POC actions. POC delete remains denied. Require expected versions and links; display—not verify—Drive access disclaimer. |
| Authorization | Pre-Sales Manager/assigned SE/Leadership request as matrix permits; Delivery Manager assigns; DevOps/Data execute/submit; Solution Engineer gets submission notification; enforce scope/team/maximum two atomically. |
| Frontend | Pending Assignment queue for Delivery Manager, assignee selection, Drive guidance, immutable submitted history, POC sequence list. |
| Tests | Multiple POCs allowed; max two concurrent assignments; wrong actor/stage/link denial; submitted immutability; no POC->RFX; notification/audit atomically emitted. |
| Risks | Current POC logic limits one POC and allows Solution Engineer execution, the exact opposite of v2. Do not patch this incrementally with generic PUTs. |
| Rollback | Retain POC tracker records and new links/history; feature-flag new routes only after migrated DTO tests pass. |

## Phase 9 — Delivery Manager workflow

| Item | Plan |
|---|---|
| Files affected | new delivery models/repository/service/controller/routes, authorization, notifications/audit, frontend Projects area, migrations/tests. |
| DB changes | Per D1/D8, create `delivery_projects` plus `delivery_assignments` with member completion/audit/version fields. Associate exactly one project to an approved win if option 2 is selected. |
| Migration required? | Yes for new aggregate. |
| API changes | Projects list/detail, Delivery Manager assign/reassign, employee mark own work done, manager mark project done. Never offer opportunity stage mutation to delivery roles. |
| Authorization | Delivery Manager active-role scope only; DevOps/Data can only mark own assignment; Leadership override per matrix; manager completion does not depend on employee flags. |
| Frontend | Projects navigation for Delivery Manager and delivery employees; show POC team as proposal, require explicit manager confirmation. |
| Tests | Team scope isolation; reassignment history; employee cannot complete others/project; manager can complete with incomplete members; concurrency. |
| Risks | The approved model requires a hard API/data boundary: the project is mutable while its originating opportunity is terminal and locked. Never make Delivery Project mutation an opportunity-update exception. |
| Rollback | New projects are append-preserved; hide feature, do not delete completed delivery history. |

## Phase 10 — RFX, Negotiations, and final approval

| Item | Plan |
|---|---|
| Files affected | stage/opportunity services and schemas, optional RFX/Negotiation models if docs need records, authorization, audit/notification, frontend action panels, migrations/tests. |
| DB changes | Add RFX document-link fields/record as D3 decides; optional lightweight negotiation metadata only if required. No mandatory NDA/MSA/SOW column. |
| Migration required? | Likely yes for RFX record/link. |
| API changes | Explicit `advance-to-rfx`, `advance-to-poc`, `advance-to-negotiations`, final Pre-Sales approval, and Close Lost/SE Closed Won request actions. |
| Authorization | Pre-Sales/assigned SE/Leadership stage permissions; final Delivery transition only Pre-Sales Manager unless D1 names a Leadership override; require valid POC context. |
| Frontend | Server-driven action buttons, Drive disclaimer, Negotiations checklist/message that documents are optional, final approval screen. |
| Tests | No skipping; RFX link timing from D3; valid POC requirement; SE approval request/reject; only final approver reaches delivery. |
| Risks | Do not add a fake Google Drive verification integration. |
| Rollback | New metadata nullable/feature-gated until use; preserve transition history. |

## Phase 11 — Closure and locking

| Item | Plan |
|---|---|
| Files affected | opportunity/stage/authorization services, schemas/routes, audit/notification, frontend action components, reports, migration/tests. |
| DB changes | Enforce outcome/lost reason/explanation/final revenue constraints and closure actor/time/version. Add a Closed Won request record if not already created in Phase 10. |
| Migration required? | Yes if Phase 2 did not add all closure fields. |
| API changes | Separate close-won, request/approve/reject-closed-won, and close-lost actions; all require expected state/version. |
| Authorization | Lead: Sales Manager/Leadership direct closure. Qualified+: Pre-Sales/Leadership; Solution Engineer Lost direct and Won request only; deny Sales Executive/Admin/Delivery. Closed locks must be enforced in every related service. |
| Frontend | Lost-reason conditional validation (`Other` needs explanation), immutable closed detail presentation, no mutation controls. |
| Tests | Every role/stage closure table cell; Other reason condition; final revenue snapshot; cross-resource closed locking; stale closures and audit. |
| Risks | “Closed Won -> Delivery” semantics remain unsafe until D1/D2 are resolved. |
| Rollback | Never erase closure/audit/final revenue. Correct via authorized forward administrative remediation only. |

## Phase 12 — Notification and audit alignment

| Item | Plan |
|---|---|
| Files affected | `ActivityService`, `NotificationService`, activity constants, models/migrations if event/outbox added, every workflow service, notification UI/tests. |
| DB changes | Add structured audit payload/version/active-role/correlation fields and optionally a transactional domain-event/outbox table. Keep existing audit rows readable. |
| Migration required? | Yes if structured columns/events are adopted. |
| API changes | Audit history DTO with safe redaction; notification types for all v2 business actions. |
| Authorization | Recheck current recipient/entity authorization on read as current `NotificationService` does; no notification should become a visibility backdoor. |
| Frontend | Clear event labels/links only when entity remains visible; no sensitive PII in messages. |
| Tests | Every required audit event; notification recipients; transaction rollback leaves neither half-written audit nor notification; stale notification handling. |
| Risks | Free-text-only audit cannot reliably prove historical field transitions. |
| Rollback | Append-only event/audit data; retain old notification mappings during transition. |

## Phase 13 — Dashboards and reporting

| Item | Plan |
|---|---|
| Files affected | dashboard/performance repositories/services/routes, frontend dashboard components, authorization/tests. |
| DB changes | Prefer indexed query fields/materialized reporting only after query profiling; no required core migration beyond earlier value/outcome/participant data. |
| Migration required? | Possibly indexes only. |
| API changes | Leadership company-wide performance; Sales Manager sourced vs participation revenue views; Sales Executive found-opportunity revenue subject to authorized scope. Retire incentive outputs. |
| Authorization | Use the same central scoped query as list/detail/search; never derive broader access from a report. |
| Frontend | Replace estimated/weighted forecast labels if those concepts are removed; role-specific, non-actionable aggregates. |
| Tests | Scope isolation, accurate final-revenue attribution, no closed/archived leakage, query performance budget. |
| Risks | Existing dashboard uses `estimated_value` and probability (`services/dashboard_service.py`/repository), which are not v2 revenue semantics. |
| Rollback | Version report endpoints/feature flags; retain legacy dashboard temporarily with explicit legacy labeling. |

## Phase 14 — Frontend v2 integration

| Item | Plan |
|---|---|
| Files affected | `frontend/src/App.jsx`, auth roles/navigation, API clients, pages/components/styles for Accounts, Opportunity Detail, RFX, POC, Negotiations, Projects, Leadership, Admin. |
| DB changes | None. |
| Migration required? | No. |
| API changes | Consume only completed server actions/DTOs; remove calls to retired generic actions/inline account creation. |
| Authorization | UI role visibility is advisory; show server-provided action availability but never invent permissions locally. |
| Frontend | Implement in vertical slices after backend phases, with accessible forms/error states/version-conflict refresh behavior/Drive disclaimers. |
| Tests | Component tests where available, route smoke tests, build, direct API authorization tests remain primary. |
| Risks | Building screens before endpoint invariants leads to frontend workarounds and authorization drift. |
| Rollback | Route/API feature flags; retain old screens only while backend compatibility remains. |

## Phase 15 — Seed data and historical migration rehearsal

| Item | Plan |
|---|---|
| Files affected | `backend/seed_data.py`, `backend/app/seed/*`, seed workbook/fixtures, docs, migrations/test data. |
| DB changes | Backfill/mapping only through reviewed migration scripts; create v2 test identities/roles/stages/accounts/participants/POCs/projects. |
| Migration required? | Yes for production historical mappings; seed scripts themselves must be idempotent. |
| API changes | None required. |
| Authorization/frontend | Seed all role combinations and active-role scenarios; avoid production-like PII in local fixtures. |
| Tests | Run seed twice; compare immutable/history counts; test all v2 flows from seed; migration rehearsal from copy of current database. |
| Risks | Two competing seed paths currently exist and legacy seed conflates creator/SE. Never run old seed after v2 cutover without compatibility guards. |
| Rollback | Database backup plus migration downgrade only where lossless; seed actions must not delete or rewrite history. |

## Phase 16 — Security, concurrency, and regression certification

| Item | Plan |
|---|---|
| Files affected | Entire backend test suite, test config/CI, migration verification scripts, frontend build checks, security docs. |
| DB changes | Add/verify indexes and constraints discovered under load; no business-schema change unless a failed invariant requires one. |
| Migration required? | Only for verified constraints/indexes. |
| API changes | Freeze/version the v2 contract; remove or hard-deny obsolete legacy mutation endpoints after client cutover. |
| Authorization | Direct HTTP tests for every denied role/resource/stage; account and notification leak tests; object-ID enumeration tests. |
| Frontend | Build/lint and manual role navigation verification; never treat it as authorization evidence. |
| Tests | PostgreSQL integration tests for migrations/partial unique indexes/row-version conflicts; parallel tests for Decision Maker, POC max-two, value changes, role changes, closure; last Leadership race; audit immutability; seed idempotency; endpoint contract and regression suite. |
| Risks | SQLite cannot prove PostgreSQL-specific locking/partial-index semantics. CI must include PostgreSQL. |
| Rollback | Release behind database-compatible feature flags where possible; preserve logs/audit and use a forward-fix plan for any data-bearing v2 feature. |

## Approval checkpoint

All decision blockers are now resolved. Wait for explicit user approval before beginning Phase 1; then execute one phase at a time: migration review -> backend tests -> API contract -> frontend slice -> migration rehearsal -> checkpoint.
