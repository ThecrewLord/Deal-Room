"""phase 2 lifecycle and transition engine

Revision ID: j1k2l3m4n5o6
Revises: i0j1k2l3m4n5
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "j1k2l3m4n5o6"
down_revision: Union[str, Sequence[str], None] = "i0j1k2l3m4n5"
branch_labels = None
depends_on = None


def _columns(bind, table):
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}

def _indexes(bind, table):
    return {i["name"] for i in sa.inspect(bind).get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()

    opp_cols = _columns(bind, "opportunities")
    additions = [
        ("lifecycle_stage", sa.Column("lifecycle_stage", sa.String(30), nullable=True)),
        ("outcome", sa.Column("outcome", sa.String(20), nullable=True)),
        ("operational_status", sa.Column("operational_status", sa.String(20), nullable=True)),
        ("review_status", sa.Column("review_status", sa.String(40), nullable=True)),
        ("lost_reason", sa.Column("lost_reason", sa.String(100), nullable=True)),
        ("lost_explanation", sa.Column("lost_explanation", sa.Text(), nullable=True)),
        ("row_version", sa.Column("row_version", sa.Integer(), nullable=True, server_default=sa.text("1"))),
    ]
    for name, column in additions:
        if name not in opp_cols:
            op.add_column("opportunities", column)

    # Preserve old stage/status semantics while deriving a deterministic v2
    # state. Closed historical rows use their latest prior non-closed stage
    # when one exists; otherwise lifecycle_stage remains NULL for explicit
    # remediation rather than inventing history.
    bind.execute(sa.text("""
        UPDATE opportunities
        SET lifecycle_stage = CASE
            WHEN stage_id IN (SELECT stage_id FROM stage_master WHERE stage_name = 'Lead / Identified') THEN 'Lead'
            WHEN stage_id IN (SELECT stage_id FROM stage_master WHERE stage_name = 'Qualification') THEN 'Qualified'
            WHEN stage_id IN (SELECT stage_id FROM stage_master WHERE stage_name = 'Discovery') THEN 'RFX'
            WHEN stage_id IN (SELECT stage_id FROM stage_master WHERE stage_name = 'POC / Technical Evaluation') THEN 'POC'
            WHEN stage_id IN (SELECT stage_id FROM stage_master WHERE stage_name IN ('Proposal', 'Negotiation')) THEN 'Negotiations'
            ELSE lifecycle_stage
        END
        WHERE lifecycle_stage IS NULL
    """))
    bind.execute(sa.text("""
        UPDATE opportunities o
        SET lifecycle_stage = (
            SELECT CASE
                WHEN sm.stage_name = 'Lead / Identified' THEN 'Lead'
                WHEN sm.stage_name = 'Qualification' THEN 'Qualified'
                WHEN sm.stage_name = 'Discovery' THEN 'RFX'
                WHEN sm.stage_name = 'POC / Technical Evaluation' THEN 'POC'
                WHEN sm.stage_name IN ('Proposal', 'Negotiation') THEN 'Negotiations'
            END
            FROM stage_history h
            JOIN stage_master sm ON sm.stage_id = h.stage_id
            WHERE h.opportunity_id = o.opportunity_id AND sm.is_closed = FALSE
            ORDER BY h.created_at DESC, h.history_id DESC
            LIMIT 1
        )
        WHERE o.lifecycle_stage IS NULL
          AND (o.status = 'Closed' OR o.is_active = FALSE)
    """))
    bind.execute(sa.text("""
        UPDATE opportunities
        SET outcome = CASE
            WHEN stage_id IN (SELECT stage_id FROM stage_master WHERE stage_name = 'Closed Won') THEN 'Closed Won'
            WHEN stage_id IN (SELECT stage_id FROM stage_master WHERE stage_name = 'Closed Lost') THEN 'Closed Lost'
            WHEN status = 'Closed' AND status <> 'Closed Won' THEN 'Open'
            ELSE 'Open'
        END
        WHERE outcome IS NULL
    """))
    bind.execute(sa.text("""
        UPDATE opportunities
        SET operational_status = CASE
            WHEN status = 'Closed' OR is_active = FALSE THEN 'Closed'
            ELSE 'Active'
        END
        WHERE operational_status IS NULL
    """))
    bind.execute(sa.text("""
        UPDATE opportunities
        SET review_status = CASE
            WHEN status = 'Pending Sales Manager Review' THEN 'Pending Sales Manager Review'
            WHEN status = 'Approved' THEN 'Approved'
            WHEN status = 'Rejected' THEN 'Rejected'
            ELSE 'Draft'
        END
        WHERE review_status IS NULL
    """))
    bind.execute(sa.text("UPDATE opportunities SET row_version = 1 WHERE row_version IS NULL"))

    # Compatibility columns now mirror the v2 operational state. They remain
    # present for legacy reports but are no longer workflow authority.
    bind.execute(sa.text("""
        UPDATE opportunities
        SET status = operational_status,
            is_active = (operational_status <> 'Closed')
    """))

    hist_cols = _columns(bind, "stage_history")
    hist_additions = [
        ("from_lifecycle_stage", sa.Column("from_lifecycle_stage", sa.String(30), nullable=True)),
        ("to_lifecycle_stage", sa.Column("to_lifecycle_stage", sa.String(30), nullable=True)),
        ("actor_active_role", sa.Column("actor_active_role", sa.String(50), nullable=True)),
        ("version", sa.Column("version", sa.Integer(), nullable=True)),
    ]
    for name, column in hist_additions:
        if name not in hist_cols:
            op.add_column("stage_history", column)

    # Existing history is historical truth. Populate only deterministic target
    # labels; never manufacture a from-stage transition for old rows.
    bind.execute(sa.text("""
        UPDATE stage_history h
        SET to_lifecycle_stage = CASE
            WHEN sm.stage_name = 'Lead / Identified' THEN 'Lead'
            WHEN sm.stage_name = 'Qualification' THEN 'Qualified'
            WHEN sm.stage_name = 'Discovery' THEN 'RFX'
            WHEN sm.stage_name = 'POC / Technical Evaluation' THEN 'POC'
            WHEN sm.stage_name IN ('Proposal', 'Negotiation') THEN 'Negotiations'
            ELSE NULL
        END
        FROM stage_master sm
        WHERE h.stage_id = sm.stage_id AND h.to_lifecycle_stage IS NULL
    """))

    bind.execute(sa.text("UPDATE stage_history SET version = 1 WHERE version IS NULL"))

    # Validate every opportunity before making the v2 state columns authoritative.
    # Unmappable historical records intentionally abort the migration rather than guess.
    invalid = bind.execute(sa.text("""
        SELECT COUNT(*) FROM opportunities
        WHERE lifecycle_stage IS NULL
           OR row_version IS NULL
           OR outcome IS NULL
           OR operational_status IS NULL
           OR review_status IS NULL
    """)).scalar()
    if invalid:
        raise RuntimeError(f"A2 migration found {invalid} opportunities with unmappable/invalid lifecycle state; remediate before v2 cutover.")

    missing_lost_reason = bind.execute(sa.text("""
        SELECT COUNT(*) FROM opportunities
        WHERE outcome = 'Closed Lost' AND (lost_reason IS NULL OR btrim(lost_reason) = '')
    """)).scalar()
    if missing_lost_reason:
        raise RuntimeError(f"A2 migration found {missing_lost_reason} Closed Lost opportunities without a historical standard reason; remediate before v2 cutover.")

    op.alter_column("opportunities", "lifecycle_stage", nullable=False)
    op.alter_column("opportunities", "outcome", nullable=False)
    op.alter_column("opportunities", "operational_status", nullable=False)
    op.alter_column("opportunities", "review_status", nullable=False)
    op.alter_column("opportunities", "row_version", nullable=False)

    for name in ("ix_opportunities_lifecycle_stage", "ix_opportunities_outcome", "ix_opportunities_operational_status", "ix_opportunities_review_status", "ix_opportunities_row_version"):
        if name not in _indexes(bind, "opportunities"):
            col = name.replace("ix_opportunities_", "")
            op.create_index(name, "opportunities", [col], unique=False)

    # PostgreSQL/modern SQLite support these checks at table level; legacy
    # values have already been normalized above.
    op.create_check_constraint("ck_opportunities_v2_outcome", "opportunities", "outcome IN ('Open','Closed Won','Closed Lost')")
    op.create_check_constraint("ck_opportunities_v2_operational_status", "opportunities", "operational_status IN ('Active','Stalled','Closed')")
    op.create_check_constraint("ck_opportunities_v2_lifecycle_stage", "opportunities", "lifecycle_stage IS NULL OR lifecycle_stage IN ('Lead','Qualified','RFX','POC','Negotiations','Delivery')")
    op.create_check_constraint("ck_opportunities_v2_closed_consistency", "opportunities", "(outcome = 'Open' AND operational_status IN ('Active','Stalled')) OR (outcome IN ('Closed Won','Closed Lost') AND operational_status = 'Closed')")


def downgrade() -> None:
    bind = op.get_bind()
    for name in (
        "ck_opportunities_v2_closed_consistency", "ck_opportunities_v2_lifecycle_stage",
        "ck_opportunities_v2_operational_status", "ck_opportunities_v2_outcome",
    ):
        try:
            op.drop_constraint(name, "opportunities", type_="check")
        except Exception:
            pass
    for name, col in (("ix_opportunities_row_version", "row_version"), ("ix_opportunities_review_status", "review_status"),
                      ("ix_opportunities_operational_status", "operational_status"), ("ix_opportunities_outcome", "outcome"),
                      ("ix_opportunities_lifecycle_stage", "lifecycle_stage")):
        if name in _indexes(bind, "opportunities"):
            op.drop_index(name, table_name="opportunities")
    for name in ("version", "actor_active_role", "to_lifecycle_stage", "from_lifecycle_stage"):
        if name in _columns(bind, "stage_history"):
            op.drop_column("stage_history", name)
    for name in ("row_version", "lost_explanation", "lost_reason", "review_status", "operational_status", "outcome", "lifecycle_stage"):
        if name in _columns(bind, "opportunities"):
            op.drop_column("opportunities", name)
