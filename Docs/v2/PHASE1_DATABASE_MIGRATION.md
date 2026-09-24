# Deal Room V2 — Phase 1 Database Migration

## Migration

`o1p2q3r4s5t6_phase1_v2_core_reset.py`

Parent: `c291f00db181`

## Purpose

Move the database to a canonical V2 lifecycle representation without silently treating legacy stage IDs as workflow authority.

## Canonical `stage_master`

| display_order | stage_name | is_closed | is_won |
|---:|---|---|---|
| 1 | Lead | false | false |
| 2 | Qualified | false | false |
| 3 | RFX | false | false |
| 4 | POC | false | false |
| 5 | Negotiations | false | false |
| 6 | Delivery | false | false |

## Migration behavior

1. Insert missing canonical V2 stages.
2. Synchronize `opportunities.stage_id` from authoritative `lifecycle_stage`.
3. Synchronize historical `stage_history.stage_id` from explicit V2 destination fields where available.
4. Validate lifecycle, outcome, operational status, review status, row version, and closed-state consistency.
5. Delete obsolete V1 stage rows only after dependent FKs are repaired.
6. Reassert canonical stage metadata.

The migration deliberately does not infer new lifecycle meaning from obsolete stage IDs. Invalid/ambiguous Opportunity state aborts the migration so an explicit disposable development reset can be performed instead.

## Development reset

```bash
python seed_v2.py --reset-demo
```

This removes disposable Opportunity-domain demo records and recreates canonical V2 demo data. It does not delete users, user roles, system permissions, or authentication/security configuration.

## Verification

```bash
flask db upgrade
alembic current
alembic heads
```

The expected result is one migration head: `o1p2q3r4s5t6`.
