"""Group 8 closure request workflow

Revision ID: 7f8e9d0c1b2a
Revises: 60ba9620bb40
Create Date: 2026-09-24 14:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f8e9d0c1b2a"
down_revision: Union[str, Sequence[str], None] = "60ba9620bb40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_closed_won_requests_opportunity",
        "closed_won_requests",
        type_="unique",
    )

    op.add_column(
        "closed_won_requests",
        sa.Column(
            "requested_outcome",
            sa.String(length=20),
            nullable=True,
            server_default="Closed Won",
        ),
    )
    op.add_column(
        "closed_won_requests",
        sa.Column("requested_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "closed_won_requests",
        sa.Column("requested_explanation", sa.Text(), nullable=True),
    )

    op.execute(
        "UPDATE closed_won_requests "
        "SET requested_outcome = 'Closed Won' "
        "WHERE requested_outcome IS NULL"
    )
    op.alter_column(
        "closed_won_requests",
        "requested_outcome",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default=None,
    )
    op.create_check_constraint(
        "ck_closed_won_requests_outcome",
        "closed_won_requests",
        "requested_outcome IN ('Closed Won', 'Closed Lost')",
    )
    op.create_index(
        "ix_closed_won_requests_requested_outcome",
        "closed_won_requests",
        ["requested_outcome"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_closed_won_requests_requested_outcome",
        table_name="closed_won_requests",
    )
    op.drop_constraint(
        "ck_closed_won_requests_outcome",
        "closed_won_requests",
        type_="check",
    )
    op.drop_column("closed_won_requests", "requested_explanation")
    op.drop_column("closed_won_requests", "requested_reason")
    op.drop_column("closed_won_requests", "requested_outcome")
    op.create_unique_constraint(
        "uq_closed_won_requests_opportunity",
        "closed_won_requests",
        ["opportunity_id"],
    )
