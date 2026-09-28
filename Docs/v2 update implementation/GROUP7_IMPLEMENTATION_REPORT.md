# Deal Room V2 — Group 7 Implementation Report

## GROUP 7 STATUS

**Implemented in the supplied backend snapshot.** Runtime test execution was not possible in this container because the environment does not have Flask installed; the source and tests pass Python compilation. The existing repository test environment must run the pytest/database verification commands below before declaring the group complete.

## 1. CURRENT SUBMISSION FLOW

Canonical existing path retained:

`POST /api/v2/pocs/<poc_id>/submit`

The route delegates to `Phase2Service.submit_poc(...)`.

Flow after implementation:

1. Load the authoritative `POCTracker` row.
2. Validate authenticated actor, active approved status, allowed role, exact POC-team membership, and open POC opportunity state.
3. Reject unknown request fields; only `result_view_link` and `row_version` are accepted.
4. Validate the result URL syntactically.
5. Validate the current `row_version`.
6. Resolve the assigned Solution Engineer from `OpportunityTeam`.
7. Perform a conditional optimistic-concurrency update of `POCTracker`.
8. Preserve the existing Group 5 `POC_SUBMITTED` history integration and existing audit architecture.
9. Commit the business mutation/audit first.
10. Only after commit, create the `POC_SUBMITTED` notification for the assigned Solution Engineer.

## 2. FILES CHANGED

- `app/auth/authorization.py`
- `app/services/phase2_service.py`
- `tests/test_collaboration_workflow.py`
- `tests/test_group7_poc_submission.py`

## 3. FILES ADDED

- `tests/test_group7_poc_submission.py`
- `GROUP7_IMPLEMENTATION_REPORT.md`

## 4. FILES REMOVED

None.

## 5. API CHANGES

The existing endpoint was retained. Submission input is now restricted to:

```json
{
  "result_view_link": "https://example.com/result",
  "row_version": 7
}
```

Client-controlled `status`, `submitted_by`, `submitted_at`, `outcome`, and `outcome_notes` are no longer accepted by the submission action.

## 6. AUTHORIZATION CHANGES

Submission now requires:

- authenticated actor
- active approved user
- active role `DevOps Engineer` or `Data Analyst`
- exact membership in the POC's team with that role
- open opportunity
- lifecycle stage `POC`
- non-closed operational status
- `outcome == Open`

The actor is taken from the authenticated service arguments; request-body identity fields are not trusted.

## 7. POC STATE CHANGES

Submission is permitted only from the existing active states:

- `Draft`
- `In Progress`

The existing status values were reused. No new POC status or POC model was introduced.

A POC with `submitted_at` already populated is rejected, preserving the first submitted result.

## 8. CONCURRENCY CHANGES

The existing `row_version` mechanism is now enforced for submission.

The update includes a database-side predicate on:

- `poc_id`
- expected `row_version`
- active POC status
- `submitted_at IS NULL`

A stale/concurrent mutation produces the existing `TransitionConflict`/HTTP 409 path. Successful submission increments `row_version` atomically.

## 9. AUDIT CHANGES

The existing `ActivityService` / `AuditLog` architecture is reused with:

`POC / POC_SUBMITTED`

The audit actor is the authenticated submitter and is committed with the POC mutation.

## 10. NOTIFICATION CHANGES

The existing `NotificationService` is reused.

The recipient is resolved from the authoritative `OpportunityTeam` Solution Engineer assignment. No request-body recipient is accepted.

The notification is created only after the POC mutation/audit transaction commits. Delivery Manager and unrelated users are not targeted by this submission action.

## 11. DATABASE/MIGRATION CHANGES

No schema change was required.

No migration was added or modified.

`60ba9620bb40_deal_room_v2_baseline.py` was not changed.

## 12. SECURITY TESTS

Added coverage for:

- assigned DevOps Engineer submission
- assigned Data Analyst submission
- unassigned POC member rejection
- unauthorized-role rejection
- client-controlled field rejection
- invalid URL rejection
- stale row-version rejection without mutation
- second normal submission rejection / result immutability
- closed-opportunity rejection
- assigned Solution Engineer notification

## 13. TEST RESULTS

### PASS

- `python -m compileall -q app tests`

### NOT RUN IN THIS CONTAINER

- pytest: unavailable because Flask is not installed in the execution environment
- `flask db check`
- `flask db heads`
- `flask db current`

### Existing baseline context

Before this Group 7 implementation, the supplied project had previously reported the Group 6 focused tests passing and one unrelated legacy Group 1 lifecycle test failure in the user's local environment. That Group 1 issue was intentionally not modified by Group 7.

## 14. KNOWN ISSUES

1. Full pytest/database verification must be run in the project's existing virtual environment.
2. Notification persistence is intentionally a separate post-commit transaction because the existing NotificationService stores notifications in the database and does not provide a post-commit publisher abstraction.
3. If notification persistence itself fails after the business commit, the POC submission remains committed; the notification transaction is rolled back and the error is propagated. No pre-commit false notification is possible.

## 15. ITEMS INTENTIONALLY LEFT FOR GROUP 5/6/8

- Group 5 POC history architecture was not redesigned.
- Group 6 repeat/new-POC workflow was not changed.
- Group 8 closure workflow was not changed.
- No new POC statuses were introduced.
- No new notification or audit architecture was introduced.
- No new concurrency mechanism was introduced.
- No POC submission replacement/retry mechanism was introduced.

## 16. COMMANDS TO RUN LOCALLY

From the backend virtual environment:

```bash
python -m pytest -q tests/test_group7_poc_submission.py
python -m pytest -q tests/test_collaboration_workflow.py
python -m pytest -q tests/ -k poc
python -m pytest -q
python -m compileall app
flask db check
flask db heads
flask db current
```

If a failure appears, classify it as Group 7, an existing/legacy test mismatch, another group, test-spec mismatch, or environment before changing unrelated code.
