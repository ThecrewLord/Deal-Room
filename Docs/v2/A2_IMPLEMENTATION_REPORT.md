# Deal Room v2 — A2 Lifecycle & Transition Engine

**Scope:** Person A / Phase A2 only  
**Status:** Implemented in the supplied working tree; PostgreSQL verification pending because no PostgreSQL test database is available in this execution environment.

## 1. Lifecycle model

### Lifecycle stage

`Lead -> Qualified -> RFX -> POC -> Negotiations -> Delivery`

No skipping and no `POC -> RFX` reopening.

### Outcome

`Open | Closed Won | Closed Lost`

Closed outcomes are not ordinary lifecycle stages.

### Operational status

`Active | Stalled | Closed`

`Closed` is terminal for normal mutation.

### Review state

A separate `review_status` preserves the initial Sales Manager review workflow without polluting operational status:

`Draft | Pending Sales Manager Review | Approved | Rejected`

## 2. Authoritative state engine

`LifecycleTransitionService` is the single mutation authority for lifecycle, outcome and operational-status changes.

The old `StageService` is now a read/compatibility facade. `OpportunityRepository.update_stage()` is retired and raises rather than mutating state directly.

All action routes require an expected integer `row_version`. The service:

1. loads the opportunity with a transaction row lock where supported;
2. rejects closed opportunities;
3. validates active-role authorization through the existing A1 `AuthorizationService` boundary;
4. checks the expected version;
5. validates the exact state edge;
6. executes any registered later-domain precondition;
7. updates state and increments `row_version` with a compare-and-swap `WHERE` clause;
8. appends transition history;
9. writes the existing `AuditLog` through `ActivityService`;
10. commits once.

Any exception before commit leaves the transaction rollbackable; no second audit/notification system was introduced.

## 3. Legacy compatibility

Historical `stage_master` rows are not renamed or deleted.

Explicit mappings are retained:

| Legacy | v2 |
|---|---|
| Lead / Identified | Lead |
| Qualification | Qualified |
| Discovery | RFX |
| POC / Technical Evaluation | POC |
| Proposal | Negotiations |
| Negotiation | Negotiations |

`stage_id`, `status`, and `is_active` remain compatibility fields. The authoritative v2 fields are `lifecycle_stage`, `outcome`, `operational_status`, `review_status`, and `row_version`.

Historical closed rows are mapped from their last deterministic non-closed stage where possible. The migration does not fabricate an unknown historical stage.

## 4. Authorization

| Action | Allowed active roles |
|---|---|
| Lead -> Qualified | Sales Manager, Leadership |
| Qualified -> RFX | Pre-Sales Manager, assigned Solution Engineer, Leadership |
| RFX -> POC | Pre-Sales Manager, assigned Solution Engineer, Leadership + registered RFX-domain precondition |
| POC -> Negotiations | Pre-Sales Manager, assigned Solution Engineer, Leadership + registered POC-domain precondition |
| Negotiations -> Delivery / final Closed Won | Pre-Sales Manager; Leadership governance override remains supported |
| Lead Closed Won/Lost | Sales Manager, Leadership |
| Qualified+ Closed Won | Pre-Sales Manager, Leadership; assigned SE Closed Won is rejected until the later approval workflow exists |
| Qualified+ Closed Lost | Pre-Sales Manager, assigned Solution Engineer, Leadership |
| Stage mutation | Admin, Sales Executive, Delivery Manager, DevOps Engineer, Data Analyst denied |

The active JWT role is the authorization input. Possessing another role does not grant its permissions.

## 5. Initial Lead review

- `submit-lead` moves review state to `Pending Sales Manager Review` while remaining at `Lead`.
- `review` with `APPROVE` requires a Sales Executive assignment and performs `Lead -> Qualified`.
- `review` with `REJECT` changes only `review_status` to `Rejected`; it does not create a lifecycle transition or close the opportunity.
- Direct Lead Closed Won/Lost actions are explicit closure actions and do not require Sales Executive assignment.

## 6. Closure and locking

Closed Won/Lost set:

```text
outcome = Closed Won | Closed Lost
operational_status = Closed
```

The lifecycle remains the current lifecycle position except that `Negotiations -> Delivery` is represented as `lifecycle_stage = Delivery` plus terminal `Closed Won`, matching the resolved D1/D2 model. Delivery Project creation remains a later phase.

Closed Lost requires a standard reason. `Other` additionally requires an explanation.

## 7. Concurrency

`row_version` is an integer beginning at `1`.

State mutations use a conditional update against the expected version. A stale version raises `TransitionConflict`, mapped by the API to HTTP `409`.

`auth_version` is untouched; it remains exclusively an authentication/session invalidation mechanism.

The legacy timestamp concurrency mechanism is no longer used by A2 lifecycle/status actions.

## 8. API contract

Explicit routes now include:

- `POST /api/opportunities/:id/submit-lead`
- `POST /api/opportunities/:id/review`
- `POST /api/opportunities/:id/advance-to-rfx`
- `POST /api/opportunities/:id/advance-to-poc`
- `POST /api/opportunities/:id/advance-to-negotiations`
- `POST /api/opportunities/:id/close-won`
- `POST /api/opportunities/:id/close-lost`
- `POST /api/opportunities/:id/mark-stalled`
- `POST /api/opportunities/:id/mark-active`

The old generic `transition-technical-stage` route and `qualify` route are removed. The generic opportunity update remains for non-state fields only and now requires `expected_version`; Marshmallow rejects arbitrary stage/status/outcome payloads.

## 9. Later-domain precondition seam

A2 does not create fake POC/RFX records.

`LifecycleTransitionService.register_precondition(from_stage, to_stage, validator)` is the integration seam for later phases. `RFX -> POC` and `POC -> Negotiations` reject through the API until the owning later domain registers its validator.

This keeps state authority centralized while preventing future developers from accidentally making a context-dependent transition unconditional.

## 10. Files changed

- `backend/app/constants/stages.py`
- `backend/app/models/opportunity/opportunity.py`
- `backend/app/models/opportunity/stage_history.py`
- `backend/app/repositories/stage_repository.py`
- `backend/app/repositories/opportunity_repository.py`
- `backend/app/auth/authorization.py`
- `backend/app/services/lifecycle_transition_service.py`
- `backend/app/services/stage_service.py`
- `backend/app/services/opportunity_service.py`
- `backend/app/controllers/opportunity_controller.py`
- `backend/app/api/opportunity_routes.py`
- `backend/app/schemas/opportunity_schema.py`
- `backend/app/seed/seed_opportunities.py`
- `backend/seed_data.py`
- `frontend/src/api/opportunityApi.js`
- `frontend/src/pages/OpportunityDetail.jsx`

## 11. Files created

- `backend/migrations/versions/j1k2l3m4n5o6_phase2_lifecycle_transition_engine.py`
- `backend/tests/test_a2_lifecycle_transition_engine.py`
- `Docs/v2/A2_IMPLEMENTATION_REPORT.md`

## 12. Verification limitations

Static Python compilation was run on the A2 Python files.

The full test suite could not execute in this environment because the required Python packages are not installed and package installation cannot reach the package index. The frontend archive contains `src/` but no `package.json`, so a frontend build cannot be executed from the supplied archive.

PostgreSQL concurrency verification is **pending**. No claim is made that SQLite proves database-level concurrency correctness.

## 13. Deferred

A2 deliberately does not implement:

- Deal Finder/participant domain
- value history/final revenue
- full closure approval/request workflow
- stakeholder/account/OEM domains
- POC record/assignment domain
- Delivery Project
- Negotiations documents
- dashboards/incentives
- full notification redesign
- POC -> RFX reopening

Those domains consume the A2 contracts rather than creating alternate lifecycle mutation paths.

## 14. A2 dashboard compatibility fix

The original dashboard repository still derived closed outcomes and pipeline
stages from legacy `stage_id`, `StageMaster.is_closed/is_won`, `status`, and
`is_active`. That is incompatible with the v2 state model. Dashboard reads are
now derived from `lifecycle_stage`, `outcome`, and `operational_status`, with
`Delivery` included explicitly in the frozen lifecycle funnel. Dashboard code
remains read-only and does not become part of the A2 transition authority.

The dashboard controller now logs the server-side exception while continuing to
return a generic error to clients.
