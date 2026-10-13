"""phase 3 opportunity lifecycle foundation

Revision ID: 9c3e7a1b4f20
Revises: 8b1f3d2a9c10
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c3e7a1b4f20"
down_revision: Union[str, Sequence[str], None] = "8b1f3d2a9c10"
branch_labels = None
depends_on = None


STAGES = [
    ("Lead / Identified", 1, False, False, False),
    ("Qualification", 2, False, False, False),
    ("Discovery", 3, False, False, False),
    ("POC / Technical Evaluation", 4, True, False, False),
    ("Proposal", 5, False, False, False),
    ("Negotiation", 6, False, False, False),
    ("Closed Won", 7, False, True, True),
    ("Closed Lost", 8, False, True, False),
]


def _table_exists(bind, name):
    return sa.inspect(bind).has_table(name)


def _seed_stages(bind):
    for name, order, requires_poc, is_closed, is_won in STAGES:
        row = bind.execute(
            sa.text("SELECT stage_id FROM stage_master WHERE stage_name = :name"),
            {"name": name},
        ).first()

        if row:
            bind.execute(
                sa.text(
                    """
                    UPDATE stage_master
                    SET display_order = :display_order,
                        requires_poc = :requires_poc,
                        is_closed = :is_closed,
                        is_won = :is_won
                    WHERE stage_id = :stage_id
                    """
                ),
                {
                    "display_order": order,
                    "requires_poc": requires_poc,
                    "is_closed": is_closed,
                    "is_won": is_won,
                    "stage_id": row[0],
                },
            )
        else:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO stage_master
                        (stage_name, display_order, requires_poc, is_closed, is_won,
                         created_at, updated_at)
                    VALUES
                        (:stage_name, :display_order, :requires_poc, :is_closed, :is_won,
                         CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                ),
                {
                    "stage_name": name,
                    "display_order": order,
                    "requires_poc": requires_poc,
                    "is_closed": is_closed,
                    "is_won": is_won,
                },
            )


def upgrade() -> None:
    bind = op.get_bind()

    # Some earlier environments created StageMaster through SQLAlchemy
    # create_all rather than through Alembic. Reuse it when present.
    if not _table_exists(bind, "stage_master"):
        op.create_table(
            "stage_master",
            sa.Column("stage_id", sa.Integer(), primary_key=True),
            sa.Column("stage_name", sa.String(length=100), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False),
            sa.Column("requires_poc", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_won", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("stage_name", name="uq_stage_master_stage_name"),
        )
        op.create_index(
            "ix_stage_master_stage_name",
            "stage_master",
            ["stage_name"],
            unique=True,
        )

    else:
        stage_columns = {
            column["name"] for column in sa.inspect(bind).get_columns("stage_master")
        }
        if "requires_poc" not in stage_columns:
            op.add_column(
                "stage_master",
                sa.Column("requires_poc", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
        if "is_closed" not in stage_columns:
            op.add_column(
                "stage_master",
                sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
        if "is_won" not in stage_columns:
            op.add_column(
                "stage_master",
                sa.Column("is_won", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
        if "created_at" not in stage_columns:
            op.add_column(
                "stage_master",
                sa.Column("created_at", sa.DateTime(), nullable=True),
            )
        if "updated_at" not in stage_columns:
            op.add_column(
                "stage_master",
                sa.Column("updated_at", sa.DateTime(), nullable=True),
            )
        bind.execute(
            sa.text(
                """
                UPDATE stage_master
                SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
                    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
                """
            )
        )

    _seed_stages(bind)

    inspector = sa.inspect(bind)
    opportunity_columns = {
        column["name"] for column in inspector.get_columns("opportunities")
    }

    if "created_by" not in opportunity_columns:
        op.add_column(
            "opportunities",
            sa.Column(
                "created_by",
                sa.Integer(),
                sa.ForeignKey("users.user_id"),
                nullable=True,
            ),
        )

    if "sales_owner_id" not in opportunity_columns:
        op.add_column(
            "opportunities",
            sa.Column(
                "sales_owner_id",
                sa.Integer(),
                sa.ForeignKey("users.user_id"),
                nullable=True,
            ),
        )

    # Indexes are created only when absent so the migration is safe against
    # environments that were previously created from the SQLAlchemy models.
    inspector = sa.inspect(bind)
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("opportunities")
    }
    if "ix_opportunities_created_by" not in existing_indexes:
        op.create_index(
            "ix_opportunities_created_by",
            "opportunities",
            ["created_by"],
            unique=False,
        )
    if "ix_opportunities_sales_owner_id" not in existing_indexes:
        op.create_index(
            "ix_opportunities_sales_owner_id",
            "opportunities",
            ["sales_owner_id"],
            unique=False,
        )

    # Normalize legacy closed labels into the Phase 3 status/stage
    # distinction. The stage carries Won/Lost semantics; status is simply
    # operationally Closed.
    bind.execute(
        sa.text(
            """
            UPDATE opportunities
            SET status = 'Closed'
            WHERE status IN ('Closed Won', 'Closed Lost')
              AND stage_id IN (
                  SELECT stage_id
                  FROM stage_master
                  WHERE is_closed = TRUE
              )
            """
        )
    )

    # Safely infer historical creator only when there is exactly one Sales
    # Executive participant. Do not invent ownership for ambiguous records.
    bind.execute(
        sa.text(
            """
            UPDATE opportunities
            SET created_by = (
                SELECT MIN(ot.user_id)
                FROM opportunity_team ot
                WHERE ot.opportunity_id = opportunities.opportunity_id
                  AND ot.role = 'Sales Executive'
            )
            WHERE created_by IS NULL
              AND (
                SELECT COUNT(*)
                FROM opportunity_team ot
                WHERE ot.opportunity_id = opportunities.opportunity_id
                  AND ot.role = 'Sales Executive'
              ) = 1
            """
        )
    )

    # Establish a baseline audit record for existing opportunities that have
    # no recorded stage history. The current stage is historical truth; no
    # stage transition is invented.
    bind.execute(
        sa.text(
            """
            INSERT INTO stage_history
                (opportunity_id, stage_id, changed_by, remarks,
                 created_at, updated_at)
            SELECT o.opportunity_id,
                   o.stage_id,
                   o.created_by,
                   'Phase 3 lifecycle baseline.',
                   COALESCE(o.created_at, CURRENT_TIMESTAMP),
                   COALESCE(o.updated_at, CURRENT_TIMESTAMP)
            FROM opportunities o
            WHERE NOT EXISTS (
                SELECT 1
                FROM stage_history h
                WHERE h.opportunity_id = o.opportunity_id
            )
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()

    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("opportunities")}
    if "ix_opportunities_sales_owner_id" in indexes:
        op.drop_index("ix_opportunities_sales_owner_id", table_name="opportunities")
    if "ix_opportunities_created_by" in indexes:
        op.drop_index("ix_opportunities_created_by", table_name="opportunities")

    columns = {column["name"] for column in inspector.get_columns("opportunities")}
    # Nullable columns can safely be removed on supported databases. The
    # migration is intentionally not destructive to stage data.
    if "sales_owner_id" in columns:
        op.drop_column("opportunities", "sales_owner_id")
    if "created_by" in columns:
        op.drop_column("opportunities", "created_by")
