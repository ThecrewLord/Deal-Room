"""A3: retain active role in audit records.

Revision ID: l3m4n5o6p7q8
Revises: k2l3m4n5o6p7
"""
from alembic import op
import sqlalchemy as sa

revision = "l3m4n5o6p7q8"
down_revision = "k2l3m4n5o6p7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("audit_logs", sa.Column("actor_active_role", sa.String(length=100), nullable=True))
    op.create_index("ix_audit_logs_actor_active_role", "audit_logs", ["actor_active_role"], unique=False)


def downgrade():
    op.drop_index("ix_audit_logs_actor_active_role", table_name="audit_logs")
    op.drop_column("audit_logs", "actor_active_role")
