"""Add closure reason to opportunities.

Revision ID: b4c5d6e7f8a9
Revises: 93e6990990fd
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, Sequence[str], None] = "93e6990990fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "opportunities",
        sa.Column("closure_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("opportunities", "closure_reason")
