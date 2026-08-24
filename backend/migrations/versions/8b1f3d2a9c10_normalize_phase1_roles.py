"""normalize phase 1 business roles

Revision ID: 8b1f3d2a9c10
Revises: 6d4dfe68c4fb
Create Date: 2026-08-12 15:48:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b1f3d2a9c10"
down_revision: Union[str, Sequence[str], None] = "6d4dfe68c4fb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User roles are stored directly as strings rather than FK references to
    # a role table. Preserve existing users by renaming only the obsolete
    # finalized role value.
    op.execute(
        """
        UPDATE user_roles
        SET role = 'Solution Engineer'
        WHERE role = 'Pre-Sales Consultant'
        """
    )

    bind = op.get_bind()
    invalid = bind.execute(
        sa.text(
            """
            SELECT DISTINCT role
            FROM user_roles
            WHERE role NOT IN (
                'Admin',
                'Sales Executive',
                'Sales Manager',
                'Pre-Sales Manager',
                'Solution Engineer',
                'Delivery'
            )
            """
        )
    ).scalars().all()

    if invalid:
        raise RuntimeError(
            "Phase 1 role migration found unsupported existing user role(s): "
            + ", ".join(map(str, invalid))
            + ". Review and migrate these values explicitly before rerunning."
        )


def downgrade() -> None:
    # This is an intentionally one-way data normalization. Reverting every
    # Solution Engineer row would also rename users who were assigned the
    # canonical role after this migration.
    pass
