# A2 Dashboard 500 Fix

## Symptom

The UI shows `Unable to load data / Failed to load dashboard` while the browser
console reports a `500 (INTERNAL SERVER ERROR)` for the dashboard request.

## Root cause

A2 made these opportunity fields authoritative:

- `lifecycle_stage`
- `outcome`
- `operational_status`
- `review_status`
- `row_version`

The old dashboard repository was still calculating metrics from the legacy
`stage_id`, `StageMaster.is_closed/is_won`, `status`, and `is_active` fields.
It also treated the legacy `StageMaster` vocabulary as the current lifecycle.
That creates an A2 integration regression and can fail immediately when the
A2 migration has not yet been applied.

The browser `VM... Uncaught TypeError ... startTime` message is not the source
of the dashboard HTTP 500. It is emitted by a browser performance/monitoring
script and is independent of the Flask dashboard exception.

## Code fix

`backend/app/repositories/dashboard_repository.py` now:

- uses v2 `outcome` for Won/Lost counts;
- uses v2 `operational_status` for open/closed pipeline filtering;
- uses v2 `lifecycle_stage` for the funnel;
- includes all six frozen lifecycle stages, including `Delivery`;
- no longer uses `StageMaster.is_closed/is_won` to determine outcomes;
- returns v2 stage names in recent opportunities;
- keeps the dashboard read-only.

`backend/app/controllers/dashboard_controller.py` now records the actual
server exception in the backend log instead of silently swallowing it.

## Required database step

The code fix does not and should not auto-run database migrations.
If the database was created before A2, run:

```bash
cd backend
alembic upgrade head
```

or the project's Flask/Alembic equivalent:

```bash
flask --app run.py db upgrade
```

Then restart the Flask backend and refresh the browser.

The A2 migration is:

```text
j1k2l3m4n5o6_phase2_lifecycle_transition_engine
```

Do not manually `ALTER TABLE` the database.

## If the dashboard still returns 500

Check the Flask backend terminal after the request. The controller now logs
`Dashboard load failed ...` together with the exception traceback. That
traceback is the authoritative next diagnostic signal.
