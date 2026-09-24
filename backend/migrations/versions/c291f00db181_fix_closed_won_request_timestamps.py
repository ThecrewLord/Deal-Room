"""Add BaseModel timestamps to closed won requests.

Revision ID: c291f00db181
Revises: n5o6p7q8r9s0
"""

from alembic import op
import sqlalchemy as sa


revision = "c291f00db181"
down_revision = "n5o6p7q8r9s0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "closed_won_requests",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.add_column(
        "closed_won_requests",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # The ORM BaseModel supplies timestamps on INSERT/UPDATE.
    # Remove the database defaults after existing/new rows are safely
    # initialized so the schema remains aligned with BaseModel behavior.
    op.alter_column(
        "closed_won_requests",
        "created_at",
        server_default=None,
    )

    op.alter_column(
        "closed_won_requests",
        "updated_at",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("closed_won_requests", "updated_at")
    op.drop_column("closed_won_requests", "created_at")