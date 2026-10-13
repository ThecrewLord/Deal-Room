# Deal Room V2 — Group 4 Implementation Report

## Status

Group 4 POC model cleanup implemented. Group 3 remains unchanged and its 8 focused tests were reported passing before Group 4 work began.

## 1. Authoritative POC model

- `app/models/opportunity/poc_tracker.py` — `POCTracker`
- `poc_tracker` remains the single authoritative POC record.
- `poc_team_members` remains the authoritative POC team relationship.
- No legacy `poc` table/model or duplicate POC service was introduced.

## 2. Fields removed from the authoritative POC model

- `objective`
- `success_metric`
- `exit_criteria`
- `failure_condition`
- `input_drive_link`

These were removed after caller audit. POC requirement/document content is no longer stored as Deal Room-owned POC data; the external RFX Drive workspace remains the source of truth.

## 3. Fields retained

- `opportunity_id`
- `poc_name`
- `status`
- `target_date` — retained because it is used by the existing POC workflow/dashboard and is not document/content data.
- `result_view_link`
- `outcome`
- `outcome_notes`
- `requested_by`
- `submitted_by`
- `submitted_at`
- `start_date`
- `end_date`
- `remarks`
- `submission_metadata`
- `row_version`
- timestamps inherited from `BaseModel`

`SolutionDesign.technical_requirements` was audited and retained because it belongs to the solution-design domain rather than `POCTracker`.

## 4. Service/API changes

- `Phase2Service.request_poc()` now accepts only POC workflow fields: `poc_name`, `target_date`, and `remarks`.
- Obsolete document/content fields are explicitly rejected rather than silently accepted.
- V2 and compatibility POC response serializers no longer expose removed fields.
- Compatibility `/api/poc` routes still delegate to `Phase2Service`; no competing POC implementation was created.
- Dashboard upcoming-POC output now uses `poc_name` instead of the removed objective.
- Search no longer queries the removed objective field; it searches retained POC name/status/outcome fields.
- POC PDF generation no longer reproduces removed requirement/document content and instead exposes the result-view reference plus existing workflow/result information.

## 5. Database migration

Revision: `8a4b6c7d9e01`

Down revision: `7f3a2c1d9e10`

Upgrade drops the five obsolete columns from `poc_tracker`.

The baseline migration `60ba9620bb40_deal_room_v2_baseline.py` was not modified.

Downgrade restores the removed columns as nullable compatibility columns; it does not attempt to reconstruct deleted historical document/content data.

## 6. Tests

Updated existing tests that constructed POCs using removed fields.

Added a regression test verifying:

- removed fields are absent from the SQLAlchemy `POCTracker` table definition;
- requests containing the obsolete fields are rejected by `Phase2Service.request_poc()`.

## 7. Verification

`python -m compileall -q app tests` passes in the build environment.

The build environment did not have Flask/dependencies installed and had no network access to install `requirements.txt`, so the full pytest/Alembic runtime checks could not be executed in this environment.

Run locally from the project's existing virtual environment:

```bash
python -m pytest -q
flask db check
flask db heads
flask db current
```

Then verify the new migration is the current head and the focused Group 3 tests remain green:

```bash
python -m pytest -q tests/test_rfx_group3.py
```

## 8. Out of scope

No POC history, repeat POC, POC submission redesign, closure changes, delivery changes, or new lifecycle transitions were implemented.
