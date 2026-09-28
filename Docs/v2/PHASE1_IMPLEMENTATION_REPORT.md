# Deal Room V2 — Phase 1 Implementation Report

**Status:** Implemented in the supplied repository; verification is split between static verification and environment-dependent runtime verification.

## 1. Scope

Phase 1 stabilizes the V2 core: lifecycle/state model, Lead submission and review, Deal Finder immutability, Leadership/Admin authorization boundaries, closure, value/final-revenue foundation, optimistic concurrency, audit/event behavior, opportunity visibility, frontend contract alignment, deterministic development seed/reset, and certification tests.

Later-domain features such as the full Accounts redesign, Stakeholders redesign, OEM CRUD, authoritative POC execution, Negotiations domain, Delivery Project, Activities/Follow-ups expansion remain Phase 2 scope.

## 2. Architecture changes

- `lifecycle_stage`, `outcome`, `operational_status`, `review_status`, and `row_version` are the authoritative Opportunity state dimensions.
- `stage_id` remains a compatibility/read/history FK but is synchronized from the canonical V2 lifecycle name and is not the workflow authority.
- Lifecycle mutation is centralized in `LifecycleTransitionService`.
- Value mutation is centralized in `OpportunityValueService`.
- Authorization is centralized in `AuthorizationService` and evaluates active-role/resource/scope/state relationships.
- Existing `ActivityService` remains the audit boundary; no second audit system was introduced.
- Existing notification infrastructure remains the event/notification boundary.
- Sensitive Opportunity mutations use integer compare-and-swap `row_version` semantics.

## 3. Lifecycle model

Canonical stages are exactly:

`Lead -> Qualified -> RFX -> POC -> Negotiations -> Delivery`

`Closed Won` and `Closed Lost` are terminal outcomes, never lifecycle stages.

The generic lifecycle service explicitly rejects `Negotiations -> Delivery`; that transition is reserved for the explicit Closed Won approval action.

## 4. Lead workflow

- Every approved active business role except Admin can create a Lead.
- The server derives Deal Finder from the authenticated actor.
- Client-supplied Deal Finder/creator/state fields are not accepted as authoritative creation inputs.
- A new Lead starts at `Lead / Open / Active / Draft / row_version=1`.
- Submission requires description, pain points, and at least one stakeholder.
- All eligible Deal Finder roles can submit their own Lead.
- Submission changes only `review_status` to `Pending Sales Manager Review` and increments the version.
- Initial review exposes exactly `Approve`, `Close Won`, and `Close Lost`.
- Sales Manager self-review is allowed.
- Lead rejection/rework is removed from the backend service, authorization, schema, notifications, and frontend.

## 5. Closure

Closed Won is allowed from any open lifecycle stage according to the frozen role matrix. Closed Lost is allowed according to the frozen stage/role matrix and requires a standard reason; `Other` additionally requires an explanation.

At closure:

- `outcome` becomes `Closed Won` or `Closed Lost`.
- `operational_status` becomes `Closed`.
- The opportunity is locked for normal mutation.
- Closed Won snapshots Final Revenue atomically from the server-side current Opportunity Value.
- Final Revenue is not client-supplied and cannot be overwritten after establishment.
- A Negotiations Closed Won approval changes lifecycle to Delivery; early Closed Won preserves the current lifecycle stage.

## 6. Value history

Current Opportunity Value can only be changed after creation by Sales Manager, Pre-Sales Manager, or Leadership. The existing immutable value-history table records old value, new value, reason, actor, active role, timestamp, and opportunity row version.

## 7. Authorization

- Leadership has company-wide opportunity visibility and system governance.
- Admin has system administration access only and receives an empty business-opportunity query.
- Active-role isolation remains server enforced through JWT `active_role`, DB role membership, and `auth_version` validation.
- Qualified onward lifecycle authority is limited to Pre-Sales Manager, assigned Solution Engineer, and Leadership, except the final Delivery gate which uses explicit Closed Won approval.

## 8. Database

Migration `o1p2q3r4s5t6_phase1_v2_core_reset.py` establishes canonical six-stage data, repairs Opportunity/StageHistory stage FKs from authoritative V2 lifecycle values, removes obsolete stage rows after FK repair, and validates impossible state combinations before completing.

The explicit development command `python seed_v2.py --reset-demo` resets disposable Opportunity-domain demo data while preserving users, roles, permissions, and authentication/security configuration.

## 9. Frontend

- Removed Lead Reject UI.
- Removed rejected Lead edit/submission assumptions.
- Added all eligible V2 business roles to business Opportunity/Account/Detail route guards.
- Lead creation controls are shown only to eligible non-Admin Deal Finder roles.
- Opportunity detail renders lifecycle stage, outcome, and operational status separately.
- Closed Lost displays the persisted `Closed Lost Remark` when available.
- Negotiations displays an explicit `Final Closed Won Approval` action for authorized users.
- The frontend remains a presentation layer; backend authorization is authoritative.

## 10. Tests

Obsolete A2-A5 and legacy lifecycle test modules were removed/replaced because they asserted V1/V2 transitional behavior such as rejected Leads and legacy stage names. A new `test_phase1_certification.py` covers roles, Deal Finder, Lead submission/review, lifecycle edges, closure, value history, locking, active-role isolation, and Leadership/Admin visibility.

## 11. Verification

Static verification completed successfully:

```bash
python -m compileall backend/backend/app backend/backend/tests
```

Runtime pytest execution could not be completed in the supplied execution environment because required Python packages were not installed and outbound package installation was unavailable.

The supplied frontend archive also has no `package.json`, Vite configuration, or lockfile, so a frontend build/lint/test command cannot be honestly claimed from this archive.

## 12. Known limitations

- PostgreSQL runtime migration and true PostgreSQL concurrency verification require the project's PostgreSQL environment; SQLite cannot certify PostgreSQL locking behavior.
- Phase 2 domain behavior is intentionally not implemented merely to make Phase 1 tests pass.
- Existing later-domain source files remain in the repository, but Phase 1 does not treat their domain-specific behavior as part of the V2 core state machine.
