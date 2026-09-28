"""add optimistic concurrency to rfx contexts

Revision ID: 7f3a2c1d9e10
Revises: 60ba9620bb40
Create Date: 2026-09-24 12:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "7f3a2c1d9e10"
down_revision = "60ba9620bb40"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "rfx_contexts",
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index(
        "ix_rfx_contexts_row_version",
        "rfx_contexts",
        ["row_version"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_rfx_contexts_row_version", table_name="rfx_contexts")
    op.drop_column("rfx_contexts", "row_version")
