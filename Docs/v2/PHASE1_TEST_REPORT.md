# Deal Room V2 — Phase 1 Test Report

## Test suite reset

Legacy tests that asserted rejected Leads, Rework, old lifecycle names, Closed Won/Closed Lost stage rows, generic stage mutation, or old Delivery-role assumptions were removed from the Phase 1 certification set.

## New certification suite

`backend/tests/test_phase1_certification.py`

Coverage includes:

- exact six-stage V2 master
- all eligible Deal Finder roles
- Admin Lead creation denial
- server-derived Deal Finder
- creation payload state-injection rejection
- pre-submission description/pain-point/stakeholder validation
- exactly three initial review decisions
- Sales Manager self-review
- sequential lifecycle edges
- forbidden generic Negotiations -> Delivery
- Closed Won from Lead and Qualified/RFX/POC/Negotiations
- Closed Lost reason and `Other` explanation
- final revenue snapshot
- value authorization/history/concurrency
- closed-state locking
- active-role isolation
- Leadership company visibility
- Admin business isolation

## Static verification

```bash
python -m compileall backend/backend/app backend/backend/tests
```

Result: pass.

## Runtime verification limitation

`pytest` could not be executed because the supplied runtime lacks project dependencies (for example Alembic/Marshmallow) and package installation failed because external network access was unavailable.

Therefore this report does **not** claim a green runtime test suite.

## Frontend verification limitation

The supplied `src` archive does not contain package metadata such as `package.json`. A frontend build/lint/test result is therefore not claimed.
