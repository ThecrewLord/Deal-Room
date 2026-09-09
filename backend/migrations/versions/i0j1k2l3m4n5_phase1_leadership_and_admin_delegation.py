"""Add v2 system-permission delegation and normalize role vocabulary.

Revision ID: i0j1k2l3m4n5
Revises: h9i0j1k2l3
"""
from alembic import op
import sqlalchemy as sa

revision = "i0j1k2l3m4n5"
down_revision = "h9i0j1k2l3"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "user_system_permissions" not in tables:
        op.create_table(
            "user_system_permissions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("permission", sa.String(length=100), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
            sa.UniqueConstraint("user_id", "permission", name="uq_user_system_permission"),
        )
        op.create_index("ix_user_system_permissions_user_id", "user_system_permissions", ["user_id"])
        op.create_index("ix_user_system_permissions_permission", "user_system_permissions", ["permission"])

    # Older databases may still contain the retired Delivery label.  Never
    # reinterpret it as Delivery Manager: the historical application used it
    # as the technical role. Convert only to the already-canonical Solution
    # Engineer role, and remove duplicate role rows safely.
    if "user_roles" in tables:
        op.execute(
            """
            DELETE FROM user_roles
            WHERE role = 'Delivery'
              AND user_id IN (
                  SELECT legacy.user_id FROM user_roles legacy
                  WHERE legacy.role = 'Delivery'
                    AND EXISTS (
                        SELECT 1 FROM user_roles current
                        WHERE current.user_id = legacy.user_id
                          AND current.role = 'Solution Engineer'
                          AND current.id <> legacy.id
                    )
              )
            """
        )
        op.execute(
            "UPDATE user_roles SET role = 'Solution Engineer' WHERE role = 'Delivery'"
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "user_system_permissions" in inspector.get_table_names():
        op.drop_index("ix_user_system_permissions_permission", table_name="user_system_permissions")
        op.drop_index("ix_user_system_permissions_user_id", table_name="user_system_permissions")
        op.drop_table("user_system_permissions")
