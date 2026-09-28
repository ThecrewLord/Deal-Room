# Deal Room V2 — Group 5 Implementation Report

## Scope
Implemented Group 5 only: lightweight immutable append-only POC business history.

Out of scope:
- Group 6 repeat POC request workflow
- POC submission redesign
- closure
- Delivery changes
- lifecycle transition changes
- Negotiations changes

## Architecture
- `POCTracker` remains the authoritative current POC state.
- `POCHistory` is a separate immutable business-history table.
- `AuditLog` / `ActivityService` remains separate from POC history.
- No `poc_attempts`, `poc_events_v2`, `poc_activity_history`, or `poc_request_history` model was introduced.

## History model
`poc_history` contains only:
- `history_id`
- `opportunity_id`
- `actor_id`
- `event_type`
- `reason`
- `created_at`

Supported event types:
- `POC_STARTED`
- `POC_SUBMITTED`
- `NEW_POC_REQUESTED`

`created_at` is database/server generated.

## Existing workflow integration
The existing backend has no separate `start_poc` business action; `request_poc()` creates a POC in `Draft`, so Group 5 does not invent a new start transition or falsely record `POC_STARTED` for a request.

The existing `Phase2Service.submit_poc()` records `POC_SUBMITTED`.

`POC_STARTED` remains a supported history event for the existing/future domain start action without adding a new Group 5 workflow.

No new POC workflow or endpoint was introduced.

`NEW_POC_REQUESTED` is supported by the history persistence helper and requires a non-blank reason, but no repeat-POC endpoint was added.

## Immutability
- ORM update/delete listeners reject normal SQLAlchemy mutation.
- PostgreSQL migration adds a database trigger rejecting UPDATE/DELETE on `poc_history`.
- There is no public PUT/PATCH/DELETE history endpoint.
- History writes are added to the same transaction as the POC mutation and the history helper never commits independently.

## Security
- Actor ID is derived from the authenticated backend `user` object.
- No request payload field is accepted as authoritative actor identity.
- History references existing `users` and `opportunities` through foreign keys.
- The helper validates that the opportunity exists.
- No history read endpoint was added, avoiding a new IDOR-prone API surface.

## Migration
New migration:
`9b5c7d1e2f34_add_poc_history.py`

Chain:
`60ba9620bb40` → `7f3a2c1d9e10` → `8a4b6c7d9e01` → `9b5c7d1e2f34`

The baseline migration was not modified.

## Tests added
- POC submission appends `POC_SUBMITTED` without overwriting start history.
- ORM mutation of history is rejected.
- `NEW_POC_REQUESTED` rejects missing/blank reasons.
- `NEW_POC_REQUESTED` accepts a non-blank reason.
- unsupported history event types are rejected.
- transaction rollback removes an uncommitted history record.

## Verification
- Python compile check passed.
- Full pytest could not be executed in the build environment because Flask is not installed there.
- Local runtime/Alembic verification should be performed in the project's existing `.venv`.
