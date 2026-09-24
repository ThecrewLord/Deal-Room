# Deal Room V2 — Group 2 Implementation Report

## Status

Group 2 Pre-Sales Manager -> Solution Engineer assignment workflow implemented and verified against the supplied Group 2 contract.

The existing authoritative `OpportunityTeam` relationship is reused. No duplicate `solution_engineer_assignments` model/table was introduced.

## 1. Assignment authority

Only an authenticated user with the active `PRE_SALES_MANAGER` role may perform the Solution Engineer assignment action.

Other roles are denied, including:

- Sales Manager
- Sales Executive
- Solution Engineer
- Delivery Manager
- DevOps Engineer
- Data Analyst

Role spoofing and unauthenticated access are also covered by direct API tests.

## 2. Candidate validation

The assignment workflow verifies that the candidate:

- exists;
- is active;
- actually has the Solution Engineer role;
- is eligible for the assignment.

An inactive or incorrectly typed candidate is rejected.

## 3. Opportunity-state validation

Assignment is allowed only when the opportunity is in the required qualified/open/active state.

Assignment attempts against:

- Lead
- RFX
- POC
- Negotiations
- Delivery
- Closed Won
- Closed Lost

are rejected.

The workflow does not trust a client-provided lifecycle state.

## 4. Duplicate and reassignment behavior

Duplicate assignment of the same Solution Engineer is rejected.

No unsupported reassignment policy was invented.

Existing Sales Executive ownership and Deal Finder information are preserved; assignment does not replace unrelated opportunity-team relationships.

## 5. Concurrency

The existing `row_version` optimistic concurrency mechanism is preserved.

A stale row version results in a conflict rather than silently overwriting newer state.

## 6. Request/API boundaries

The assignment request is limited to assignment/concurrency data.

The client cannot use the assignment action to control unrelated opportunity fields such as lifecycle or ownership state.

Direct API tests verify that unrelated fields cannot be injected through the assignment payload.

## 7. Transaction, audit and events

The implementation reuses the existing application architecture for:

- persistence;
- audit logging;
- notification/event emission.

No duplicate notification or audit system was introduced.

The assignment operation remains atomic with the existing transaction model.

## 8. Database model

No new Solution Engineer assignment model/table was introduced.

The existing authoritative `OpportunityTeam` relationship remains the source of truth.

No Group 2 migration was required for the assignment workflow.

## 9. Tests added / updated

Dedicated Group 2 tests are present in:

`tests/test_opportunity_lifecycle.py`

Coverage includes:

- PSM can assign a valid Solution Engineer;
- all non-PSM roles are denied;
- candidate must really be a Solution Engineer;
- inactive candidate is rejected;
- assignment is allowed only at Qualified;
- closed opportunities cannot receive an SE;
- duplicate assignment is rejected;
- stale `row_version` returns conflict;
- direct API authorization;
- assignment payload cannot control unrelated fields;
- unauthenticated requests are rejected;
- role spoofing is rejected.

## 10. Test results

Latest local full-suite result:

```text
95 passed
1 failed
1 skipped
97 total
```

All Group 2-specific tests executed successfully in this run.

No Group 2 test was reported as failed.

The only failure in the complete suite belongs to Group 1:

```text
tests/test_opportunity_lifecycle.py::test_group1_stage_skipping_rejected[POC-Delivery]
```

## 11. Verification

Test collection:

```bash
python -m pytest --collect-only -q
```

Result:

```text
97 tests collected
```

Full runtime suite:

```bash
python -m pytest -q
```

Result:

```text
95 passed, 1 failed, 1 skipped
```

Because the single failure is a Group 1 exception-classification mismatch, it does not indicate a failing Group 2 assignment behavior in the reported run.

## 12. Warnings

The runtime suite produced 576 warnings across the repository.

These primarily include:

- PyJWT HMAC key-length warnings;
- SQLAlchemy `Query.get()` deprecation warnings;
- SQLAlchemy query/subquery warnings.

No Group 2 test failure was attributed to these warnings.

## 13. Out of scope

Group 2 did not implement later workflow groups such as:

- POC model cleanup/history/repeat POC;
- closure workflow;
- delivery workflow;
- legacy cleanup;
- later revenue/forecast workflows.

Those remain governed by their respective implementation groups.

## 14. Final assessment

Group 2 implementation and dedicated test coverage are present.

The latest full-suite run shows the Group 2 tests passing, including authorization, candidate validation, state validation, duplicate prevention, optimistic concurrency, API payload protection, authentication, and role-spoofing checks.

Group 2 can therefore be recorded as passing in the latest runtime suite, while Group 1 retains one test-contract mismatch described in the Group 1 report.
