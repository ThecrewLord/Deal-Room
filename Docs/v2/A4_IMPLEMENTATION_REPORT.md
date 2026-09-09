# Deal Room v2 — A4 Implementation Report

## Scope

A4 adds the authoritative Opportunity Value mutation boundary, append-only value history, Final Revenue persistence/finality, revenue attribution reporting contracts, API endpoints, minimal Opportunity Detail UI wiring, and focused security/integrity tests.

## Source note

The supplied backend/src archives were inspected as the current implementation source. The requested `A1/A2/A3` architecture was preserved. The File Library contained the A3 implementation report, which confirms `Opportunity.created_by` is immutable Deal Finder and `sales_owner_id` is separate. The six named `Docs/v2/*` files were not present in the supplied repository/archive and were not silently recreated.

## A. Existing value architecture

Before A4, `Opportunity.estimated_value` was already the Opportunity Value field and was stored as PostgreSQL/SQLAlchemy `NUMERIC(15,2)`. A3 creation derives it from the creation request and derives `created_by` from the authenticated active-role context.

The generic opportunity update schema previously accepted `estimated_value`, although the service's allowed-field set did not actually persist it. A4 removes `estimated_value` from the generic update contract and routes all post-creation value changes through `OpportunityValueService`.

A3's ownership semantics remain unchanged:

- `created_by` = immutable Deal Finder.
- `sales_owner_id` = Sales Executive assignment.

## B. Files changed

Backend:

- `app/auth/authorization.py`
- `app/api/opportunity_routes.py`
- `app/controllers/opportunity_controller.py`
- `app/models/__init__.py`
- `app/models/opportunity/__init__.py`
- `app/models/opportunity/opportunity.py`
- `app/schemas/opportunity_schema.py`
- `app/services/opportunity_service.py`
- `app/services/lifecycle_transition_service.py`

Frontend:

- `src/api/opportunityApi.js`
- `src/pages/OpportunityDetail.jsx`

## C. Files created

- `app/models/opportunity/opportunity_value_history.py`
- `app/services/opportunity_value_service.py`
- `migrations/versions/m4n5o6p7q8r9_a4_value_history_revenue.py`
- `tests/test_a4_value_history_revenue.py`
- `A4_IMPLEMENTATION_REPORT.md`

## D. Value model

```text
Initial Opportunity Value
    = Opportunity.estimated_value at creation
    = set by authenticated Deal Finder
    ↓
Current Opportunity Value
    = mutable Opportunity.estimated_value
    = only Sales Manager / Pre-Sales Manager / Leadership
    ↓
Closed Won
    ↓
Final Revenue
    = server-captured current Opportunity Value
    = Opportunity.final_revenue
    = immutable after establishment
```

New opportunities receive one initial history record:

```text
old_value = null
new_value = initial estimated_value
reason = Initial Opportunity Value
actor_id = Deal Finder
actor_active_role = authenticated active role
opportunity_row_version = 1
```

Existing historical opportunities are not backfilled with fabricated actor/reason data.

## E. Authorization matrix

| Active role | Change Opportunity Value |
|---|---|
| Leadership | YES, within visible resource scope |
| Sales Manager | YES, within visible resource scope |
| Pre-Sales Manager | YES, within visible resource scope |
| Sales Executive | NO |
| Solution Engineer | NO |
| Delivery Manager | NO |
| DevOps Engineer | NO |
| Data Analyst | NO |
| Admin | NO |

Authorization uses A1's active-role context and the existing opportunity visibility policy. A multi-role user receives no union of permissions.

## F. Value history

`OpportunityValueHistory` stores:

```text
history_id
opportunity_id
old_value
new_value
reason
actor_id
actor_active_role
changed_at
opportunity_row_version
created_at
updated_at
```

There are no update, patch, or delete value-history endpoints. The migration additionally installs PostgreSQL triggers that reject UPDATE/DELETE against the history table.

## G. Concurrency

Value mutation requires `expected_version` and uses the existing Opportunity `row_version`.

Mutation boundary:

```text
SELECT opportunity FOR UPDATE
→ active-role/resource authorization
→ expected_version check
→ server-read old value
→ optimistic compare-and-swap UPDATE
→ row_version + 1
→ history INSERT
→ AuditLog INSERT via ActivityService
→ commit
```

A stale compare-and-swap produces `409 Conflict`. The value/history/audit writes are in one transaction; unexpected failures roll the transaction back.

History records the successful post-mutation version. Example: version 12 → 13 produces history version 13.

## H. Generic update protection

`OpportunityUpdateSchema` no longer accepts `estimated_value` or `final_revenue`.

`OpportunityService.update_opportunity()` also explicitly rejects direct service-level attempts to provide either field, so an internal caller cannot accidentally turn the generic CRUD path into a value mutation path.

The frontend Opportunity Detail sales editor no longer submits the value field through generic `PUT /opportunities/{id}`.

## I. Final Revenue

`Opportunity.final_revenue` is nullable until Closed Won.

Existing A2 `close_won()` and the existing `Negotiations → Delivery / Closed Won` terminal path were minimally extended so Final Revenue is captured from server-side `estimated_value` in the same transaction as closure. Clients cannot provide the amount.

A PostgreSQL trigger rejects any later change to an already-established Final Revenue value.

Closed Lost does not establish Final Revenue.

## J. Revenue attribution

No incentive, commission, bonus, payout, or compensation calculation was implemented.

### Sourced Revenue

For a Sales Executive:

```text
SUM(Final Revenue)
WHERE outcome = Closed Won
AND the Sales Executive is Opportunity.created_by
```

### Participation Revenue

For a Sales Executive:

```text
SUM(Final Revenue)
WHERE outcome = Closed Won
AND the Sales Executive is present in OpportunityTeam
```

The participation relationship reuses the existing `OpportunityTeam` model; no new participant domain was created.

Reporting endpoint:

```text
GET /api/opportunities/revenue
```

- Sales Executive: returns their own sourced and participation revenue.
- Sales Manager: returns per-direct-Sales-Executive rows.
- Leadership: returns per-active-Sales-Executive rows.
- Other roles: denied.

## K. API

```text
POST /api/opportunities/{id}/value
GET  /api/opportunities/{id}/value-history
GET  /api/opportunities/revenue
```

Value request:

```json
{
  "new_value": 750000,
  "reason": "Updated commercial estimate",
  "expected_version": 12
}
```

The server determines actor, active role, timestamp, and old value.

## L. Frontend

Opportunity Detail now:

- shows Final Revenue when present;
- provides value editing only to Sales Manager, Pre-Sales Manager, and Leadership while the opportunity is open;
- requires a new value and reason;
- sends the current `row_version` as `expected_version`;
- displays read-only value history;
- does not expose an editable Final Revenue field;
- does not allow Sales Executive generic editing of Opportunity Value.

No full revenue dashboard was introduced.

## M. Tests

Focused A4 test file added:

```text
tests/test_a4_value_history_revenue.py
```

Coverage includes:

- initial value history;
- authorized roles;
- forbidden roles;
- active-role isolation;
- mandatory reason;
- server-derived old value;
- stale-version conflict;
- closed-state value lock;
- Final Revenue capture;
- absence of history mutation routes;
- sourced/participation revenue semantics;
- generic schema protection.

### Environment verification

```text
Python compileall / AST parse: PASS
Focused pytest: BLOCKED
Full pytest regression: BLOCKED
PostgreSQL migration execution: BLOCKED
PostgreSQL concurrency verification: BLOCKED
Frontend build: BLOCKED
```

The supplied execution environment did not have Flask installed and did not have Docker installed. The supplied `src` archive also contains `src/` but no `package.json`, so an actual Vite build cannot be honestly claimed from this archive alone.

The migration revision chain was statically inspected and A4 revision `m4n5o6p7q8r9` correctly points to `l3m4n5o6p7q8`.

## N. Security attack results

Static/API-contract protections implemented for attempts to manipulate:

- `estimated_value` through generic PUT → rejected by schema/service boundary;
- `final_revenue` through generic PUT → rejected by schema/service boundary;
- `old_value` → no accepted request field and server derives old value;
- `actor_id` → no accepted request field;
- `actor_active_role` → no accepted request field;
- `created_by` → unchanged and excluded from update contract;
- `sales_owner_id` → unchanged and excluded from update contract;
- `row_version` → only accepted as expected-version precondition;
- history UPDATE/DELETE → no API route and PostgreSQL trigger protection in migration.

Live HTTP/PostgreSQL attack execution remains unverified because the supplied execution environment lacks the required Flask/PostgreSQL/Docker runtime.

## O. Remaining risks

1. PostgreSQL migration has not been executed in this environment.
2. PostgreSQL trigger enforcement has not been live-tested here.
3. True concurrent HTTP transactions have not been live-tested here.
4. Full backend regression has not run because Flask is unavailable.
5. Frontend build has not run because the supplied src archive has no project wrapper/package manifest.
6. The six named `Docs/v2/*` files were not available in the supplied archive/File Library search, so no unsupported details from those files were invented.
7. Existing dashboard/performance repositories still use `estimated_value` for open-pipeline analytics, which is correct for current pipeline value; closed revenue reporting should use `final_revenue` as the A4 revenue contract.

## P. A5 / Closure integration contract

Future closure logic must not create a second value or revenue mutation service.

For Closed Won:

```text
Closure authorization/state transition
        ↓
load/lock Opportunity
        ↓
assert opportunity is open
        ↓
Final Revenue = current server-side estimated_value
        ↓
terminal Closed Won state
        ↓
commit atomically
```

The existing A2 closure boundary now performs this capture. Future closure work should preserve that boundary and extend it only for closure-specific approval/business rules.

After `final_revenue` is non-null, neither the value endpoint nor generic Opportunity CRUD may modify it. PostgreSQL trigger protection provides an additional database-level immutability boundary.

## A4 completion status

A4 implementation is **code-complete for the requested scope**, but **not fully runtime-verified** in this execution environment. The critical unverified items are explicitly listed above rather than being represented as passing tests.
