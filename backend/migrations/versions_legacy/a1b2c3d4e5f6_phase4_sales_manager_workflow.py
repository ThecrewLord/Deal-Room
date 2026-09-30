"""phase 4 sales manager opportunity workflow

Revision ID: a1b2c3d4e5f6
Revises: 9c3e7a1b4f20
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9c3e7a1b4f20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    opportunity_indexes = {index["name"] for index in inspector.get_indexes("opportunities")}
    if "ix_opportunities_status" not in opportunity_indexes:
        op.create_index(
            "ix_opportunities_status",
            "opportunities",
            ["status"],
            unique=False,
        )

    if not inspector.has_table("notifications"):
        op.create_table(
            "notifications",
            sa.Column("notification_id", sa.Integer(), primary_key=True),
            sa.Column("recipient_user_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False),
            sa.Column("notification_type", sa.String(length=100), nullable=False),
            sa.Column("entity_type", sa.String(length=50), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("notifications")}
    if "ix_notifications_recipient_user_id" not in indexes:
        op.create_index(
            "ix_notifications_recipient_user_id",
            "notifications",
            ["recipient_user_id"],
            unique=False,
        )
    if "ix_notifications_notification_type" not in indexes:
        op.create_index(
            "ix_notifications_notification_type",
            "notifications",
            ["notification_type"],
            unique=False,
        )
    if "ix_notifications_entity_id" not in indexes:
        op.create_index(
            "ix_notifications_entity_id",
            "notifications",
            ["entity_id"],
            unique=False,
        )
    if "ix_notifications_is_read" not in indexes:
        op.create_index(
            "ix_notifications_is_read",
            "notifications",
            ["is_read"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    opportunity_indexes = {index["name"] for index in inspector.get_indexes("opportunities")}
    if "ix_opportunities_status" in opportunity_indexes:
        op.drop_index("ix_opportunities_status", table_name="opportunities")

    if not inspector.has_table("notifications"):
        return
    indexes = {index["name"] for index in inspector.get_indexes("notifications")}
    for name in (
        "ix_notifications_is_read",
        "ix_notifications_entity_id",
        "ix_notifications_notification_type",
        "ix_notifications_recipient_user_id",
    ):
        if name in indexes:
            op.drop_index(name, table_name="notifications")
    op.drop_table("notifications")
