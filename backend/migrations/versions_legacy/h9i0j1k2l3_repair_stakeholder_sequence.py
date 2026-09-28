"""Repair stakeholder primary-key sequence after seeded/imported data.

Revision ID: h9i0j1k2l3
Revises: g8h9i0j1k2l3
"""
from alembic import op

revision = "h9i0j1k2l3"
down_revision = "g8h9i0j1k2l3"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Seed/import jobs may insert rows before the serial sequence is aligned.
    # Reset it to the current maximum ID so the next normal INSERT cannot
    # collide with an existing stakeholder row.
    op.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('stakeholders', 'stakeholder_id'),
            COALESCE((SELECT MAX(stakeholder_id) FROM stakeholders), 1),
            EXISTS (SELECT 1 FROM stakeholders)
        )
        """
    )


def downgrade():
    pass
