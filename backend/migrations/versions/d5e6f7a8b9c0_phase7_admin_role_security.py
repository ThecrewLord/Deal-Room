"""phase7 admin role security

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
"""
from alembic import op
import sqlalchemy as sa

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("users")}
    if "auth_version" not in cols:
        op.add_column("users", sa.Column("auth_version", sa.Integer(), nullable=True, server_default="1"))
        op.execute("UPDATE users SET auth_version = 1 WHERE auth_version IS NULL")
        op.alter_column("users", "auth_version", nullable=False, server_default=None)

def downgrade():
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("users")}
    if "auth_version" in cols:
        op.drop_column("users", "auth_version")
