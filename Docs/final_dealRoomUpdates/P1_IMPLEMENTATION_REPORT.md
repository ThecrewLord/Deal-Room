# P1 Implementation Report — Deal Room Workflow Correctness and Concurrency

## Baseline audit

The supplied backend uses Flask, SQLAlchemy, Alembic, Marshmallow, and pytest. The frontend is a React/Vite JSX application. The docs ZIP contains the existing v2 implementation reports and group-level reports.

Existing pieces verified before implementation:
- `Opportunity` carries `row_version`, `value_version`, `estimated_value`, `final_revenue`, `probability`, `expected_close_date`, `description`, `pain_points`, and server-maintained timestamps.
- `OpportunityService.update_opportunity` already uses a conditional SQLAlchemy `UPDATE` with `row_version == expected_version`, but stale conflicts were generic runtime errors and updates did not explicitly set `updated_at`.
- `OpportunityValueService.change_value` already implements conditional version updates and append-only `OpportunityValueHistory`, but contained an unconditional early rejection that made all post-creation value changes impossible.
- `LifecycleTransitionService` uses `with_for_update()` for lifecycle mutations.
- `POCTracker` has a per-POC `row_version`; `Phase2Service.submit_poc` already uses a conditional update.
- `POCHistory` is append-only, but the event check allowed only POC_STARTED, POC_SUBMITTED, and NEW_POC_REQUESTED.
- `Phase2Service.complete_poc` previously set Success/Failure without requiring a reason or checking the client row version atomically.
- `Phase2Service.request_poc` lacked an explicit active-POC guard and a database-level one-open-POC constraint.
- Stakeholder model/service initially had no independent row version; the parent opportunity's `row_version` is used as the shared concurrency token for stakeholder updates.

## Changes made

### Backend
- Updated opportunity-edit authorization so accessible, open opportunities can be edited by Sales Executives and Sales Managers, while preserving closed-opportunity locking.
- Removed the unconditional rejection in `OpportunityValueService.change_value`. Value edits still validate numeric precision/range, require a reason, use atomic `row_version` conditional updates, append value-history records, and do not change `final_revenue`.
- Explicitly update `updated_at` on opportunity and opportunity-value conditional updates.
- Convert stale ordinary opportunity updates into `TransitionConflict` / HTTP 409 and include latest version, timestamp, and latest audit actor where available.
- Added `GET /api/opportunities/<id>/metadata` for lightweight version/timestamp/last-editor polling.
- Stakeholder updates now require the parent opportunity's `expected_version` and atomically increment the parent `row_version`; stale updates roll back and return HTTP 409. The response exposes `opportunity_version`.
- Require POC completion outcome to be Success or Failure, a trimmed non-empty reason (maximum 2,000 characters), and the expected POC `row_version`. Completion uses an atomic conditional update and appends a `POC_COMPLETED` immutable history event.
- Block initial POC creation when an unresolved POC already exists, lock the opportunity where supported, and translate duplicate-open-POC integrity failures to conflicts.
- Require a completed Failure POC with a non-empty outcome reason before requesting a repeat cycle, preserving the existing failure-driven repeat policy. The previous POC record and history are not overwritten.
- Added migration `c6d7e8f9a0b1_p1_poc_integrity.py` to add the partial unique index enforcing at most one Draft/In Progress/Submitted POC per opportunity and permit `POC_COMPLETED` history events. Migration intentionally stops with an explicit error if pre-existing duplicate unresolved POCs are found; it does not delete or rewrite those records.

### Frontend
- Updated Deal Overview to show Current Opportunity Value, Expected Close, Probability, Description, Pain Points, Version, and Last Updated.
- Exposed Deal Overview editing to Sales Executives and Sales Managers on open opportunities.
- Exposed current-value editing to those roles through the existing value endpoint, preserving append-only value history.
- Added 25-second metadata polling, focus/online refresh, hidden-tab pause, and listener/timer cleanup. Full opportunity data is fetched only after metadata detects a change when the user is not editing.
- Added a conflict banner that preserves unsaved Deal Overview/value input, shows latest version/time/editor where available, and provides an explicit reload action.
- Added mandatory outcome-reason input to POC completion and sends the POC row version with the completion request.

## Files changed

- `backend/app/auth/authorization.py`
- `backend/app/services/opportunity_service.py`
- `backend/app/services/opportunity_value_service.py`
- `backend/app/services/phase2_service.py`
- `backend/app/services/stakeholder_service.py`
- `backend/app/schemas/stakeholder_schema.py`
- `backend/app/api/poc_routes.py`
- `backend/app/controllers/opportunity_controller.py`
- `backend/app/api/opportunity_routes.py`
- `backend/app/models/opportunity/poc_tracker.py`
- `backend/app/models/opportunity/poc_history.py`
- `backend/migrations/versions/c6d7e8f9a0b1_p1_poc_integrity.py`
- `backend/tests/test_group7_poc_submission.py`
- `backend/tests/test_opportunity_lifecycle.py`
- `src/api/opportunityApi.js`
- `src/pages/OpportunityDetail.jsx`
- `src/styles/opportunities.css`

## API contract changes

- Added `GET /api/opportunities/<id>/metadata`, returning `row_version`, `updated_at`, and `last_updated_by` for visible opportunities.
- `PUT /api/opportunities/<id>` continues to require `expected_version`; stale writes now return HTTP 409 with `latest_version`, `updated_at`, and `last_updated_by` when available.
- POC completion requests now require `outcome`, `outcome_notes`, and `row_version`; validation failures are distinguishable from stale-version conflicts on the v2 endpoint.
- `PUT /api/stakeholder/<id>` now requires `expected_version` (the parent opportunity's `row_version`) and returns `opportunity_version` in the stakeholder response. Existing clients that update stakeholders must include this field.

## Verification status

- Python syntax compilation: passed for all 181 backend Python files.
- JSX/JavaScript syntax transpilation of `OpportunityDetail.jsx` using the available TypeScript parser: passed.
- Backend pytest suite: **not executed successfully**. Collection stopped with missing runtime dependencies including Flask, Flask-JWT-Extended, and Marshmallow in the provided execution environment. No test pass is claimed.
- Frontend build/test: **not run**. The supplied `src` ZIP does not include `package.json` or a test/build manifest.
- Alembic upgrade and downgrade: **not executed** because backend dependencies are unavailable. Migration graph was inspected statically; the new revision continues from existing head `b4c5d6e7f8a9`.
- Genuine multi-session database race tests: not run in this environment. The partial unique index is the database-level guard for concurrent open POC creation; production PostgreSQL verification is still required.
- Stakeholder update concurrency is implemented through the parent opportunity version. Stakeholder creation and deletion do not yet require a client-supplied expected version, so the full stakeholder-mutation concurrency requirement remains partially implemented.

## Operational notes

1. Before applying the migration, run a read-only query for multiple unresolved POCs per opportunity. If duplicates exist, resolve them explicitly according to business ownership; the migration will fail rather than silently discard records.
2. In the backend virtual environment, run the existing pytest suite, then `flask db upgrade`, `flask db current`, and `flask db heads`.
3. Restore the frontend's normal package manifest/build environment and run its build and regression tests.
4. Run a PostgreSQL integration test with two separate sessions attempting to create/repeat POCs for the same opportunity, and a two-client stale-version test for opportunity updates.
