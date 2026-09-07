# Deal Room v2 Implementation Audit

**Inspection date:** 2026-09-04  
**Scope:** repository code, migrations, seed scripts, tests, and React client as present in the working tree. The v2 artifacts were used only as comparison requirements. No application code was changed for this audit.

## Executive finding

This is a useful Phase 1–10-era foundation, not a v2 implementation. It already has a Flask app factory, SQLAlchemy/Alembic, JWTs with a server-validated active role, centralized `AuthorizationService`, explicit workflow endpoints for several mutations, audit rows, notifications, and a Vite/React UI. Keep those architectural seams.

However, the active business model is materially incompatible with v2: five roles rather than nine; no Leadership; legacy stages; `created_by`/`sales_owner_id` ownership; account visibility derived from opportunity visibility; no value history, final revenue, pain points, stakeholder tags, account archive, OEM opportunity association, delivery-project model, or v2 POC team workflow. The most important implementation blockers are recorded in [V2_DECISIONS_REQUIRED.md](V2_DECISIONS_REQUIRED.md).

## 1. Repository architecture

- Monorepo layout: `backend/` Flask service and `frontend/` Vite React application. Root `backend.zip`, `backend2.zip`, `backend3.zip`, `src.zip`, etc. are historical archives, not the live source tree.
- Backend dependencies/configuration: `backend/requirements.txt`, `backend/alembic.ini`, and `backend/.env`; application factory is `backend/app/__init__.py:create_app`.
- Client dependencies/scripts are `frontend/package.json`; `npm run build` succeeds in the inspected tree (2026-09-04) with only Vite’s >500 KB chunk warning.
- The tree was already dirty when inspected (`git status --short` showed changes in backend, frontend, ZIP, and docs files). This audit neither attributes nor overwrites those changes.

## 2. Backend architecture

- Flask registers route blueprints in `backend/app/__init__.py:create_app`: auth, opportunities, accounts, stakeholders, POCs, OEM, activity/audit, notifications, dashboards, search, solution design, and performance reports.
- Layering exists: `api/*_routes.py` -> controller -> service -> repository/model. Examples: `backend/app/api/opportunity_routes.py`, `controllers/opportunity_controller.py`, `services/opportunity_service.py`, and `repositories/opportunity_repository.py`.
- SQLAlchemy is initialized once in `backend/app/database/__init__.py`; migrations use Flask-Migrate via `backend/app/database/migrate.py` and `backend/migrations`.
- `ActivityService.log` in `backend/app/services/activity_service.py` writes `AuditLog`, so the named “activity” history is audit infrastructure, not a scheduled follow-up/activity model.

## 3. Frontend architecture

- `frontend/src/App.jsx` defines client routes; `DashboardLayout`, `ProtectedRoute`, and `RoleRoute` compose role-gated pages. `RoleRoute` uses `activeRole`, which is appropriate for UX but not a security control.
- Canonical client roles are hard-coded in `frontend/src/auth/roles.js` and mirror the backend’s five-role vocabulary, not v2.
- Navigation is role-specific in `frontend/src/config/navigation.js`.
- `frontend/src/api/*.js` wraps Axios endpoints. There is a detected client/server mismatch: `frontend/src/api/pocApi.js:updatePocDesign` calls `PATCH /api/poc/:id/design`; this does exist in `backend/app/api/poc_routes.py`, despite the audit’s earlier working-tree snapshot showing a truncated route display. The create-opportunity UI in `frontend/src/pages/Opportunities.jsx` still implements an inline “Other” account path and calls `createAccount`, directly conflicting with v2.
- Existing UI centers on Opportunities, Sales Manager Review, Pre-Sales assignment, Solution Engineer POC work, simple Accounts, and Admin pages. No Leadership, RFX, Negotiations, Delivery Project, value-history, or v2 POC/delivery workspace exists.

## 4. Database schema and migrations

The base schema is defined in `backend/migrations/versions/128d06af2ba3_initial_migration.py`; subsequent migrations are Phase 1–9/cleanup deltas.

| Current table/model | Evidence | v2 relevance |
|---|---|---|
| `users`, `user_roles` | `models/auth/user.py`, `user_role.py` | Multi-role user relation exists; no Leadership invariant/delegated-admin capability. |
| `accounts` | `models/account/account.py` | Canonical descriptive fields exist, but only `is_active`; no archive metadata/canonical matching key. |
| `opportunities` | `models/opportunity/opportunity.py` | Account, creator, sales owner, stage/value/status fields exist; lacks deal-finder semantics, outcome, operational status model, pain points, final revenue/version. |
| `opportunity_team` | `models/opportunity/opportunity_team.py` | Generic current membership only; unique `(opportunity_id,user_id,role)` but no membership history/end timestamp/title taxonomy. |
| `stage_master`, `stage_history` | `models/opportunity/stage_master.py`, `stage_history.py` | Reusable master/history pattern, but old stage catalog and no from/to/outcome event payload. |
| `stakeholders` | `models/opportunity/stakeholder.py` | Single `influence_level`; no company/job-title rename/tags association/Decision Maker DB constraint. |
| `poc_tracker` | `models/opportunity/poc_tracker.py` | Main active POC model; some POC audit fields, no required v2 links/team association/immutable result enforcement at database level. |
| `poc` | `models/poc/poc.py` | A second orphan model/table with no FK and no route/service use; migration `6d4dfe68c4fb...` created it. |
| `oem_partners` | `models/account/oem_partner.py` | OEM is currently account-scoped and includes contact PII; no opportunity-OEM join. |
| `audit_logs`, `notifications` | `models/system/audit_log.py`, `notification.py` | Reusable append-oriented records; audit lacks structured before/after/correlation/version data. |
| `contacts`, `tags`, `solution_design` | model folders and migrations | Contacts/tags are not connected to v2 stakeholder behavior; SolutionDesign is a useful technical artifact but has no stated v2 lifecycle role. |

Migration chain evidence:

- `9c3e7a1b4f20_phase3_opportunity_lifecycle.py` added `created_by`/`sales_owner_id` and rewrote the stage workflow.
- `a1b2c3d4e5f6_phase4_sales_manager_workflow.py` added notifications.
- `b2c3d4e5f6a7_phase5_pre_sales_assignment.py` and `c4d5e6f7a8b9_phase6_technical_poc_workflow.py` add legacy technical ownership/POC fields.
- `f7a8b9c0d1e2_unify_delivery_into_solution_engineer.py` deliberately maps/removes legacy Delivery into Solution Engineer, which is the opposite of v2’s Delivery Manager/DevOps/Data split.
- `g8h9i0j1k2l3_remove_legacy_poc_approval_workflow.py` removes old POC approval fields.

## 5. Current roles and hierarchy

- Backend constants (`backend/app/constants/roles.py`) expose only `Admin`, `Sales Executive`, `Sales Manager`, `Pre-Sales Manager`, and `Solution Engineer`; `DELIVERY` is aliased to `Solution Engineer`, and the legacy string `Delivery` is normalized into that role.
- Frontend matches the same five in `frontend/src/auth/roles.js`.
- `User.manager_id` self-references `users`; manager compatibility is calculated in `backend/app/constants/organizations.py` and validated by `AuthService._validate_manager_assignment` in `backend/app/services/auth_service.py`.
- There is no `Leadership`, `Delivery Manager`, `DevOps Engineer`, or `Data Analyst`; no delegated-permission model. `AuthService._is_last_active_admin` protects the last Admin, not the last Leadership.

## 6. Current authorization architecture

- JWT access claims include an `active_role`; `AuthorizationService.current_context` in `backend/app/auth/authorization.py` reloads the user, checks approved/active/revoked status, `auth_version`, active-role validity, and membership. This correctly avoids unioning multiple role permissions.
- `phase2_auth_required` and `business_access_required` wrap routes. The latter blocks Admin from business paths.
- Resource scope is centralized in `AuthorizationService.opportunity_query`; it derives IC visibility from `OpportunityTeam`, Sales Manager scope from early display order/sales owner, and Pre-Sales scope from technical membership/stage. `SearchService.search` reuses the opportunity/account scope query (`backend/app/services/search_service.py`).
- **High-risk defect:** `AuthorizationService.account_query` derives accounts from visible opportunities. Employees therefore cannot search/view a centralized account unless they already see an opportunity using it. This fails v2’s central directory and is a confidentiality design error if “fixed” by exposing account-linked opportunities. Account endpoints must remain identity-only and must never join or reveal opportunities.
- Current mutation checks are partially centralized, but v2’s role + scope + stage + field + state matrix cannot be expressed safely by the current coarse methods (`can_update_opportunity`, `can_mutate_related`, `can_change_technical_stage`).

## 7. Current lifecycle implementation

- Stage constants in `backend/app/constants/stages.py`: `Lead / Identified`, `Qualification`, `Discovery`, `POC / Technical Evaluation`, `Proposal`, `Negotiation`, `Closed Won`, `Closed Lost`.
- `StageService.TECHNICAL_TRANSITIONS` in `backend/app/services/stage_service.py` permits `Qualification -> Discovery -> POC/Proposal -> Negotiation -> closed`, materially conflicting with v2’s Lead -> Qualified -> RFX -> POC -> Negotiations -> Delivery.
- Lead creation in `OpportunityService.create_opportunity` immediately creates `Lead / Identified`. The creator (Sales Executive only) can `qualify`; then can submit in `Qualification`. This violates v2’s Sales Manager approval from Lead.
- `OpportunityService.review_opportunity` accepts only `APPROVE` or `REJECT` (`OpportunityReviewSchema`); approval assigns a sales owner and later sends work to Pre-Sales. It has no initial Close Won/Lost action.
- Technical transitions and closure are explicit endpoints (`/transition-technical-stage`, `/close-won`, `/close-lost`) but authorization gives only assigned Solution Engineer authority. `StageService.close_opportunity` permits closing only from legacy `Negotiation`.
- `status` is overloaded (`Open`, `Pending Sales Manager Review`, `Approved`, `Active`, `Rejected`, `Closed`) and `is_active` duplicates closure state. V2 requires separate lifecycle, outcome, and operational status.

## 8. Opportunity ownership model

- `Opportunity.created_by` and `sales_owner_id` are separate FKs in `backend/app/models/opportunity/opportunity.py`; creation assigns `created_by` to the authenticated Sales Executive in `OpportunityService.create_opportunity`.
- An initial `OpportunityTeam` membership is created with `role=active_role`; sales assignment later creates a Sales Executive team member in `OpportunityService.review_opportunity`.
- `created_by` is not database-immutable and generic `PUT /api/opportunities/:id` does not accept it today only because `OpportunityUpdateSchema` excludes it; a future broad schema could silently mutate it. There is no named immutable Deal Finder or assignment-history model.
- `backend/app/seed/seed_opportunities.py` assigns a Sales Executive as creator and team member, confirming seed assumptions conflate creator with sales participation.

## 9. Current stakeholder model

- `Stakeholder` uses `stakeholder_name`, `designation`, email, phone, `influence_level`, and notes (`backend/app/models/opportunity/stakeholder.py`). Schemas restrict one `influence_level` to `Decision Maker`, `Influencer`, `User`, or `Blocker` (`backend/app/schemas/stakeholder_schema.py`).
- `StakeholderService` provides generic create/update/delete guarded by `AuthorizationService.can_mutate_related` (`backend/app/services/stakeholder_service.py`). It has no backend transaction-safe one-Decision-Maker constraint, no tag relation, no company field, no closed lock, and no structured audit of changed tags.

## 10. Current account model

- Account has name, industry, contact/location fields and a Boolean `is_active` (`backend/app/models/account/account.py`). Name is exact-case database unique only.
- `AccountService.create` permits only Sales Executive and creates/reuses only an exact trimmed name (`backend/app/services/account_service.py`). It does not normalize punctuation/case/legal suffixes and can create duplicates such as the v2 examples.
- `AccountController` returns canonical contact/location fields but no opportunities (`backend/app/controllers/account_controller.py`), which is a good starting boundary.
- `frontend/src/pages/Opportunities.jsx` adds an account from the opportunity form through `account_id === "other"`; this is prohibited in v2.
- No edit/archive endpoint or account audit action exists.

## 11. Current OEM model

- `OEMPartner` belongs to `Account`, not Opportunity, and includes `contact_person`, email, phone, and notes (`backend/app/models/account/oem_partner.py`).
- `OEMController.get_all/get_by_id` serializes those contact fields to any authorized business viewer (`backend/app/controllers/oem_controller.py`). This is an information-disclosure vulnerability against v2: employees must only see OEM names attached to opportunities.
- `OEMService` currently denies all mutation (`backend/app/services/oem_service.py`), so Leadership CRUD is absent.

## 12. Current POC model and workflow

- The active route/service uses `POCTracker`, not the separate `Poc` model: `backend/app/services/poc_service.py` and `backend/app/api/poc_routes.py`.
- Assigned Solution Engineers request, design, start, submit, and complete POCs. `PocService.request_poc` requires objective, success metric, exit criteria, target date, and failure condition; it does **not** require an input Drive link. `submit_result` records outcome fields but does **not** store a result view link.
- `PocService.get_eligible_opportunities` excludes any opportunity that already has a POC (`and not POCTracker...first()`), so multiple POCs are impossible through that flow.
- POC delete is denied (`PocService.delete_poc`), a useful v2-aligned behavior. But draft and in-progress POCs are mutable via generic design update; submitted status is only protected by service conditions, not a DB-level immutable snapshot/event design.
- The debug `print` in `PocService.request_poc` writes user and opportunity identifiers to stdout; remove/replace with controlled structured logging before production.
- No Delivery Manager pending-assignment worklist, max-two team constraint, DevOps/Data execution, input/result link workflow, or POC assignment history exists.

## 13. Current delivery model

- There is no DeliveryProject, delivery assignment, member completion, or Delivery Manager role/model.
- The legacy delivery role was deliberately unified into `Solution Engineer` by `f7a8b9c0d1e2_unify_delivery_into_solution_engineer.py` and `backend/app/constants/roles.py`.
- Some legacy API parameters remain (`delivery_ids` in `PreSalesAssignmentSchema`), but `OpportunityService.finalize_pre_sales_assignment` currently validates only the unified Solution Engineer model. This is stale semantic debt, not v2 delivery support.

## 14. Notification architecture

- `NotificationService.queue` writes notifications in callers’ existing transactions, and workflow services commonly log audit + queue + commit together. This is a good single-path basis.
- Visibility rechecks recipient, notification type’s expected role, and current entity authorization in `NotificationService._visible`; it avoids showing stale/unauthorized business notifications.
- `ROLE_BY_NOTIFICATION` only maps legacy workflow events (`backend/app/services/notification_service.py`): review, sales owner, technical assignment, and POC events. V2 events for Delivery Manager, Closed Won requests/final approval, account/OEM/role changes are absent.
- The system has no durable domain-event/outbox table. A database transaction succeeds atomically for its local audit/notification rows, but there is no retryable external delivery mechanism should email/webhook delivery be added.

## 15. Audit architecture

- `AuditLog` stores entity type/id, action, free-text description, actor, and base timestamps (`backend/app/models/system/audit_log.py`); `ActivityService.log` writes it.
- Major legacy workflow methods call it: opportunity creation/review/assignment, stage transition, POC actions, and user-role/admin actions. `StageHistory` separately records stage IDs and actor.
- Gaps: no structured before/after values, no immutable business event ID, no actor active role, no request/correlation ID, and many generic entity mutations only write descriptive strings. No audit exists for v2-only concepts because they do not exist.

## 16. Current concurrency implementation

- `ConcurrencyManager.has_conflict` compares client timestamp to `updated_at` in `backend/app/utils/concurrency.py`. Opportunity update, manager review, technical assignment, technical stage, close, POC actions, solution design, role changes, and stakeholder update use variants of this check.
- **Risk:** this is timestamp-based rather than an integer/row-version compare-and-swap. Precision/timezone serialization differences can cause false success/failure; two concurrent requests can both read the same timestamp and both commit without a SQL `WHERE version = :expected` guard. `StakeholderService.update_stakeholder` uses direct equality rather than the shared helper.
- There is no concurrency protection for account create/duplicate normalization, Decision Maker (not modeled), POC team membership (not modeled), OEM association (not modeled), or notifications marked read.

## 17. Current API endpoints

All registered blueprints are in `backend/app/__init__.py`; routes below come from `backend/app/api/*_routes.py`.

| Area | Endpoints (method) | Notes |
|---|---|---|
| Auth/admin | `/api/auth/signup`, login, select-role, me, refresh, logout; `/admin/pending`, users, manager-candidates, approve, roles, manager, revoke | Active role is server validated; Admin-only management exists. |
| Opportunities | collection create/list; detail/read/update/delete; stage history; qualify; submit/review queues; review; Pre-Sales assignment; technical transition; close won/lost | Legacy lifecycle; generic PUT remains present. |
| Accounts | list/create/detail | Account scope is opportunity-derived; no archive/edit/search-specific API. |
| Stakeholders | create/detail/by-opportunity/update/delete | Generic CRUD; no tags. |
| POCs | request/eligible/detail/by-opportunity/design PATCH/start/submit/complete/delete/download | No v2 assignment/link endpoints. |
| OEM | list/detail/create/update/delete | Mutations denied in service; responses disclose contact PII. |
| Other | activity history, notifications/list-read, dashboard, search, solution-design, performance reports | Dashboard/report models use estimated/probability data. |

## 18. Current seed-data assumptions

- `backend/app/seed/seed_opportunities.py` creates a lead with an approved Sales Executive as `created_by` and `OpportunityTeam` member; it uses legacy initial stage and `estimated_value`.
- `backend/seed_data.py:seed_users` creates Admin plus the five old business roles, including `delivery@dealroom.local` with `Solution Engineer`; no Leadership/Delivery Manager/DevOps/Data identities.
- `backend/seed_data.py:seed_stages` reads the legacy `PIPELINE_STAGES` constants. `seed_oem.py` and the spreadsheet loader include OEM contact data.
- `backend/app/seed/run_seed.py` only invokes admin, stage, and opportunity seeds; `seed_users.py`, `seed_accounts.py`, and `seed_poc.py` are empty. `backend/seed_data.py` is a separate richer loader. These competing seed paths are a deployment/data-integrity risk and must be consolidated/idempotently migrated for v2.

## 19. Current tests and verification result

- Tests are in `backend/tests/`: roles, authorization, lifecycle, sales-manager, pre-sales assignment, POC, integration, admin management, dashboard, and phase-10 search/security tests.
- Test coverage is legacy-oriented. It validates active-role selection, Admin business denial, older delivery aliases, old technical workflow, some audit/notification behavior, and basic timestamp conflicts. It does not cover v2 roles, Leadership invariants, value history, canonical account matching, stakeholder tags, final revenue, v2 delivery, or DB-level concurrency.
- Running `PYTHONPATH=. ../.venv/bin/pytest -q tests` from `backend/` produced **6 failures, 11 passes, 97 setup errors**. Most setup errors occur because `Config` calls `load_dotenv()`/reads `DATABASE_URL` at import time (`backend/app/config/config.py`), so tests that monkeypatch SQLite later still use the `.env` PostgreSQL URL at `127.0.0.1:5433`. Static failures include stale expectations for `Delivery`, `DELIVERY_ASSIGNED`, an old dashboard URL, and an incorrect frontend parent path. The suite is not a reliable regression gate as checked in.

## 20. Security risks and required treatment

| Severity | Evidence / realistic failure | Impact | Recommended design | Blocks v2? |
|---|---|---|---|---|
| Critical | OEM controller returns contact person/email/phone to business users (`controllers/oem_controller.py`) | Employee can obtain partner contact PII contrary to policy | Split master/admin DTO from employee opportunity-name DTO; never expose contact fields outside Leadership | Yes, before OEM exposure |
| High | Accounts are scoped through visible opportunities (`AuthorizationService.account_query`) | Central directory fails; naive fix can become opportunity-discovery backdoor | Dedicated account-directory query/DTO with no opportunity metadata | Yes, before Accounts rollout |
| High | No database compare-and-swap/version column (`utils/concurrency.py`) | Concurrent value/tag/team/close writes can silently overwrite or violate cardinality | Integer `row_version` + SQL conditional update/locking/unique partial indexes | Yes, before sensitive v2 actions |
| High | Legacy stage/outcome/status are conflated (`Opportunity.status`, `is_active`, legacy `StageMaster`) | Unauthorized/invalid state combinations and incorrect reporting become likely | Separate lifecycle stage, outcome, operational status and explicit transition engine | Yes |
| High | Generic PUT remains (`api/opportunity_routes.py`, `OpportunityUpdateSchema`) | Future schema expansion can accidentally permit protected fields via one broad path | Replace sensitive modifications with purpose-specific action endpoints and field allowlists | Yes |
| Medium | POC request logs identifiers to stdout (`PocService.request_poc`) | Sensitive operational information enters ungoverned logs | Remove debug print; structured, redacted logging only | No, but fix early |
| Medium | `Poc` is a second unreferenced POC table (`models/poc/poc.py`) | Developers or migrations can write to the wrong source of truth | Verify data, deprecate/remove only via reversible migration after cutover | No, but resolve in POC phase |
| Medium | Default secrets in `Config` | Misconfigured deployment can use publicly guessable JWT/Flask keys | Fail startup outside explicit local development when secrets unset | No, operational hardening |

## 21. Principal v2 conflicts

1. Roles/hierarchy/Leadership: `constants/roles.py` is five-role legacy; `AuthService` protects last Admin, not last Leadership.
2. Lifecycle: `constants/stages.py` and `StageService.TECHNICAL_TRANSITIONS` use Discovery/Proposal/Negotiation and allow wrong v2 paths.
3. Lead review: creator qualifies/submits from Qualification; v2 requires Deal Finder submit Lead and Sales Manager approve/close from Lead.
4. Ownership: `created_by` has Sales Executive semantics, not immutable, eligible Deal Finder; `sales_owner_id` is not a titled participant history.
5. Current value/revenue: only mutable `estimated_value`, probability/forecast dashboard fields; no reason/history/final revenue.
6. Accounts: role-limited creation and opportunity-derived visibility; inline UI creation; no normalized duplicate/archive policy.
7. Stakeholders: legacy single influence level and generic delete; no tags/Decision Maker uniqueness.
8. OEM: account-scoped relationship, contact PII disclosure, no Leadership CRUD/opportunity association.
9. POC: Solution Engineer executes, max-one flow, no Drive-link/team/delivery handoff; correct no-delete intent can be retained.
10. Delivery: removed rather than modeled; no v2 delivery project/workflow.
11. Audit/notification: infrastructure is reusable but sparse/legacy event definitions.
12. Tests/configuration: test suite doesn’t start isolated databases and asserts old semantics.

## 22. KEEP / MODIFY / REPLACE / DELETE / NEW

| Classification | Components | Action |
|---|---|---|
| KEEP | Flask app factory, SQLAlchemy, Alembic, JWT mechanics, active-role session principle, repositories/controllers, `StageHistory`, audit/notification tables, authorized search pattern | Preserve seams; extend deliberately. |
| MODIFY | `AuthorizationService`, `AuthService`, `OpportunityService`, `StageService`, `Account`, `Opportunity`, `OpportunityTeam`, `Stakeholder`, `POCTracker`, Dashboard/Search, notifications/audit, seed loader/tests/frontend roles/routes | Align each to v2, do not create parallel systems. |
| REPLACE | Legacy stage constants/transition map, broad opportunity mutation path for sensitive fields, ownership semantics of `sales_owner_id`, account query policy, POC executor workflow, legacy report meanings | Introduce explicit v2 policy/action models while preserving historic records. |
| DELETE (after migration/cutover) | Retired Delivery alias, old UI inline account flow, stale old-stage active workflow, duplicate unused `poc` table only after data verification, incentive/forecast assumptions if no retained reporting use | Deprecate first; do not physically erase historical data merely because semantics changed. |
| NEW | Leadership/delegation, new roles/hierarchy, version columns, deal finder/participants history, outcome/status/revenue/value history, account canonical/archive data, stakeholder tags + uniqueness, OEM junction/DTOs, RFX/Negotiations, POC assignment/link/result, DeliveryProject, domain events/outbox, v2 reports/tests/UI | Implement in the phased plan. |

## 23. Migration risks and strategy

1. **Do not rewrite stages in place before mapping existing records.** Add v2 state columns/transition metadata and stage mapping; preserve `stage_master`/`stage_history` legacy names for historical audit. Backfill an explicitly labeled legacy mapping and report unmappable records.
2. **Do not repurpose `created_by` silently.** Add an immutable `deal_finder_id` (initially backfilled from `created_by` with an audited migration marker) and a new participant/history relation; retain legacy `sales_owner_id` until all dependent APIs/reports are migrated.
3. **Adopt integer versions rather than timestamp-only control.** Add non-null version columns with defaults; make action endpoints require expected version and execute conditional updates in one transaction.
4. **Protect data before adding unique constraints.** Normalize prospective account keys and identify collisions before making the unique constraint. Build stakeholder tag migration and resolve multiple historical decision makers before a partial unique index.
5. **Separate OEM master from association.** Preserve existing OEM contact records under Leadership-only master access; create `opportunity_oem_partner` rather than reassigning OEMs from account to opportunity.
6. **POC duplication risk.** Inventory both `poc` and `poc_tracker` tables in the real PostgreSQL database before deciding retention/migration; code inspection alone proves only tracker is active.
7. **Seed cutover.** Consolidate `app/seed` and `seed_data.py`; never allow a seed to rewrite historical Deal Finder, participant, revenue, or stage history.
8. **Rollback.** Every schema phase should have an Alembic downgrade where safe, but data-migration reversals must be lossless or documented as forward-only after a backup/validation checkpoint.

## 24. Recommended implementation order

Follow [V2_IMPLEMENTATION_PLAN.md](V2_IMPLEMENTATION_PLAN.md), with two gates before changing application models:

1. resolve all decisions in [V2_DECISIONS_REQUIRED.md](V2_DECISIONS_REQUIRED.md), especially Closed Won/Delivery;
2. make the test factory reliably read a fixture-specific database URL and establish a migration/database snapshot procedure.

Then implement authorization/roles before exposing new UI or data routes; build the state/value/ownership invariants server-side and migrate seeds/tests before frontend expansion. The current backend has enough structure to evolve safely, but v2 must be an explicit migration, not a renamed legacy workflow.

