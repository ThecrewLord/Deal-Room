# P2 Migration Notes

Migration: `d7e8f9a0b1c2_opportunity_poc_team.py`

- Parent revision: `c6d7e8f9a0b1`
- Creates `opportunity_poc_team_members` as the canonical opportunity-level POC team.
- Enforces unique membership per `(opportunity_id, user_id)` and limits member role values to `DevOps Engineer` or `Data Analyst`.
- Backfills from the earliest POC cycle that actually has team members for each opportunity.
- Retains the existing `poc_team_members` rows. These remain per-cycle execution snapshots for legacy POC APIs and historical POC cycles.
- Downgrade removes only the canonical table and its indexes; it does not modify the old POC team records.

Inspect `flask db current` and `flask db heads` before applying. Apply using `flask db upgrade`; do not use `flask db stamp` to simulate an upgrade.
