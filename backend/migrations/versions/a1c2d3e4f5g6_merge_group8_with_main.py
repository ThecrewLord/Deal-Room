"""Merge the Group 8 closure migration branch with the main V2 migration chain.

Revision ID: a1c2d3e4f5g6
Revises: 9b5c7d1e2f34, 7f8e9d0c1b2a
"""
from typing import Sequence, Union

from alembic import op

revision: str = "a1c2d3e4f5g6"
down_revision: Union[str, Sequence[str], None] = ("9b5c7d1e2f34", "7f8e9d0c1b2a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
