"""Phase 1 V2 core reset: canonical lifecycle/stage state and constraints.

Revision ID: o1p2q3r4s5t6
Revises: n5o6p7q8r9s0
"""
from alembic import op
import sqlalchemy as sa

revision = "o1p2q3r4s5t6"
down_revision = "c291f00db181"
branch_labels = None
depends_on = None

STAGES = [
    ("Lead", 1, False, False, False),
    ("Qualified", 2, False, False, False),
    ("RFX", 3, False, False, False),
    ("POC", 4, True, False, False),
    ("Negotiations", 5, False, False, False),
    ("Delivery", 6, False, False, False),
]


def upgrade():
    bind = op.get_bind()

    # Add canonical stage rows first so all FK references can be repaired.
    for name, order, requires_poc, is_closed, is_won in STAGES:
        bind.execute(sa.text("""
            INSERT INTO stage_master (stage_name, display_order, requires_poc, is_closed, is_won, created_at, updated_at)
            SELECT :name, :ord, :poc, :closed, :won, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            WHERE NOT EXISTS (SELECT 1 FROM stage_master WHERE stage_name = :name)
        """), {"name": name, "ord": order, "poc": requires_poc, "closed": is_closed, "won": is_won})

    # The V2 lifecycle columns are authoritative. Repair stage_id from them;
    # never infer lifecycle/outcome from legacy stage IDs during cutover.
    bind.execute(sa.text("""
        UPDATE opportunities o
        SET stage_id = sm.stage_id
        FROM stage_master sm
        WHERE sm.stage_name = o.lifecycle_stage
          AND o.lifecycle_stage IN ('Lead','Qualified','RFX','POC','Negotiations','Delivery')
    """))

    # Repair historical stage references from the explicit V2 destination where
    # available. For legacy-only rows, map the old stage name deterministically.
    bind.execute(sa.text("""
        UPDATE stage_history h
        SET stage_id = sm.stage_id
        FROM stage_master sm
        WHERE sm.stage_name = h.to_lifecycle_stage
          AND h.to_lifecycle_stage IN ('Lead','Qualified','RFX','POC','Negotiations','Delivery')
    """))

    # Any remaining historical stage references are mapped by their old name.
    bind.execute(sa.text("""
        UPDATE stage_history h
        SET stage_id = sm.stage_id
        FROM stage_master old_sm
        JOIN stage_master sm ON sm.stage_name = CASE old_sm.stage_name
            WHEN 'Lead / Identified' THEN 'Lead'
            WHEN 'Qualification' THEN 'Qualified'
            WHEN 'Discovery' THEN 'RFX'
            WHEN 'POC / Technical Evaluation' THEN 'POC'
            WHEN 'Proposal' THEN 'Negotiations'
            WHEN 'Negotiation' THEN 'Negotiations'
            WHEN 'Closed Won' THEN 'Negotiations'
            WHEN 'Closed Lost' THEN 'Negotiations'
        END
        WHERE h.stage_id = old_sm.stage_id
          AND old_sm.stage_name NOT IN ('Lead','Qualified','RFX','POC','Negotiations','Delivery')
    """))

    # Closed Won/Lost are outcomes, never stages. Any remaining opportunity
    # referencing an obsolete stage is repaired from its authoritative lifecycle.
    invalid = bind.execute(sa.text("""
        SELECT COUNT(*) FROM opportunities
        WHERE lifecycle_stage IS NULL
           OR lifecycle_stage NOT IN ('Lead','Qualified','RFX','POC','Negotiations','Delivery')
           OR outcome NOT IN ('Open','Closed Won','Closed Lost')
           OR operational_status NOT IN ('Active','Stalled','Closed')
           OR review_status NOT IN ('Draft','Pending Sales Manager Review','Approved')
           OR row_version IS NULL
    """)).scalar()
    if invalid:
        raise RuntimeError(f"Phase 1 V2 migration found {invalid} invalid opportunity state rows. Use the explicit development V2 reset before retrying.")

    inconsistent = bind.execute(sa.text("""
        SELECT COUNT(*) FROM opportunities
        WHERE (outcome = 'Open' AND operational_status NOT IN ('Active','Stalled'))
           OR (outcome IN ('Closed Won','Closed Lost') AND operational_status <> 'Closed')
           OR (operational_status = 'Closed' AND outcome = 'Open')
    """)).scalar()
    if inconsistent:
        raise RuntimeError(f"Phase 1 V2 migration found {inconsistent} impossible outcome/status combinations; remediate via the explicit development reset.")

    # Remove obsolete stage rows only after every FK reference has been moved.
    bind.execute(sa.text("""
        DELETE FROM stage_master
        WHERE stage_name NOT IN ('Lead','Qualified','RFX','POC','Negotiations','Delivery')
    """))

    # Re-assert canonical metadata in case a prior seed created stale flags.
    for name, order, requires_poc, is_closed, is_won in STAGES:
        bind.execute(sa.text("""
            UPDATE stage_master
            SET display_order=:ord, requires_poc=:poc, is_closed=:closed, is_won=:won,
                updated_at=CURRENT_TIMESTAMP
            WHERE stage_name=:name
        """), {"name": name, "ord": order, "poc": requires_poc, "closed": is_closed, "won": is_won})


def downgrade():
    # Do not recreate obsolete V1 stage semantics during downgrade. The V2
    # migration is intentionally one-way for development/demo cutover safety.
    raise RuntimeError("Phase 1 V2 core reset cannot be downgraded to obsolete V1 lifecycle stages.")
