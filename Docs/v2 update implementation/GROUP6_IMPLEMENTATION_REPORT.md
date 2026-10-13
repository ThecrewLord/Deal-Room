# Deal Room V2 — Group 6 Implementation Report

## Scope

Implemented Group 6 only: Repeat POC / New POC Request workflow.

## Files changed

- `app/services/phase2_service.py`
  - Added `Phase2Service.request_new_poc()`.
  - Reuses the authoritative `POCTracker`, `POCTeamMember`, `OpportunityTeam`, `POCHistoryService`, and `NotificationService`.
  - Creates a new POC cycle for repeat work while preserving the previous submitted/completed POC and its result data.
  - Reuses the existing DE/DA team from the latest POC; no new `OpportunityTeam` assignment model is introduced.
  - Uses the latest POC `row_version` as the optimistic-concurrency token and carries it forward to the new POC cycle.
  - Performs history, new POC, team membership, activity, and notification writes in one transaction.

- `app/auth/authorization.py`
  - Added `AuthorizationService.can_request_new_poc()`.
  - Requires authenticated active `Solution Engineer`, assignment to the opportunity, opportunity visibility, open outcome, and POC lifecycle stage.

- `app/services/notification_service.py`
  - Added `NEW_POC_REQUESTED` notification type for both `DevOps Engineer` and `Data Analyst`.
  - Extended the existing notification visibility check to support a set of allowed recipient roles.
  - No second notification framework was introduced.

- `app/api/phase2_routes.py`
  - Added:
    - `POST /api/v2/opportunity/<opportunity_id>/pocs/request-new`

- `tests/test_collaboration_workflow.py`
  - Added focused Group 6 tests covering authorization, actor spoofing, IDOR, reason validation, stale row version, invalid lifecycle/closed states, transaction rollback, team preservation, notification isolation, and repeated requests/history.

## Files added

- `GROUP6_IMPLEMENTATION_REPORT.md`

## Database

No migration was required.

Group 5 already provides the required immutable `poc_history` structure and `NEW_POC_REQUESTED` event support.

## API

Endpoint:
`POST /api/v2/opportunity/<opportunity_id>/pocs/request-new`

Request body:
```json
{
  "reason": "Customer requested another validation cycle",
  "row_version": 1
}
```

Authorization:
- authenticated user
- active role must be `Solution Engineer`
- actor must be assigned to the requested opportunity as Solution Engineer
- opportunity must be visible to the actor
- opportunity must be open and in `POC`
- an existing submitted/completed POC and existing POC team are required

The endpoint does not accept `actor_id`, `user_id`, `role`, `event_type`, `created_at`, or assignment/member fields.

Response:
- `201` with the newly-created POC cycle
- `403` for authorization failures
- `409` for validation/concurrency conflicts under the existing route error conventions

## Workflow

1. Authenticate and derive the actor from the request context.
2. Lock the opportunity and latest POC record.
3. Validate active Solution Engineer authorization and opportunity state.
4. Require a non-blank reason.
5. Compare the supplied `row_version` with the latest POC version.
6. Reuse the existing DE/DA team from the latest POC.
7. Create a new `POCTracker` cycle in `Draft`.
8. Carry the POC aggregate version forward by one.
9. Append `NEW_POC_REQUESTED` to immutable `poc_history`.
10. Create the normal activity record.
11. Notify only the existing POC team.
12. Commit atomically.

The opportunity remains in `POC`. No Negotiations transition, closure, Delivery Project creation, or Delivery Manager assignment is triggered.

## Security

Implemented:
- active-role enforcement
- opportunity-level authorization
- relationship-scoped Solution Engineer assignment check
- actor identity derived from authentication
- request-body rejection for actor/role spoofing fields
- cross-opportunity IDOR protection
- closed/wrong-stage rejection
- existing POC/team validation
- notification recipient isolation

## History

Each successful repeat request creates a separate immutable:

`NEW_POC_REQUESTED`

event containing:
- `opportunity_id`
- authenticated `actor_id`
- event type
- trimmed reason
- server/database-generated timestamp

Previous history and submitted POC result data are not overwritten.

## Notifications

Recipients are exactly the existing POC team members on the latest POC, i.e. the existing DevOps Engineer and/or Data Analyst team.

The Delivery Manager is not notified for repeat POC requests.

The existing `NotificationService` is reused.

## Concurrency

The request must supply the current latest POC `row_version`.

On success, the new POC cycle receives `latest.row_version + 1`.

A retry using the previous/stale version therefore receives the project's `409` concurrency response and cannot create another repeat request from stale state.

## Transaction

The new POC cycle, copied existing team membership, history event, activity record, and notifications are written in the same database transaction.

If a required operation fails, the service rolls the transaction back so partial repeat-POC state is not left behind.

## Tests

### Static verification

- `python -m compileall -q app tests` — PASS
- AST parsing of all changed Python files — PASS

### Pytest

Attempted:

```bash
python -m pytest -q tests/test_collaboration_workflow.py -k group6
```

Result: NOT EXECUTED beyond test collection because the build/runtime environment does not have Flask installed:

```text
ModuleNotFoundError: No module named 'flask'
```

This is classified as an **environment/setup issue**, not a Group 6 test failure.

The full pytest suite was therefore not claimed as passing.

## Out-of-scope findings

- Existing first-POC workflow still notifies the Delivery Manager through `POC_REQUESTED`; this was intentionally left unchanged because Group 6 only distinguishes repeat POC behavior.
- No lifecycle, RFX, closure, Negotiations, Delivery Project, frontend, or Group 5 architecture changes were made.
