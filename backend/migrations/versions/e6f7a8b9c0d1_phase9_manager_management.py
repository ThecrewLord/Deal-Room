"""phase9 manager management

Adds the existing User.manager_id relationship to managed migration state and
ensures it is indexed. The migration is intentionally additive and preserves
existing user values.
"""
from alembic import op
import sqlalchemy as sa

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "users" not in tables:
        return

    columns = {c["name"] for c in inspector.get_columns("users")}
    if "manager_id" not in columns:
        op.add_column(
            "users",
            sa.Column("manager_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=True),
        )

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("users")}
    if "ix_users_manager_id" not in indexes:
        op.create_index("ix_users_manager_id", "users", ["manager_id"], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in set(inspector.get_table_names()):
        return

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("users")}
    if "ix_users_manager_id" in indexes:
        op.drop_index("ix_users_manager_id", table_name="users")

    columns = {c["name"] for c in sa.inspect(bind).get_columns("users")}
    if "manager_id" in columns:
        op.drop_column("users", "manager_id")
