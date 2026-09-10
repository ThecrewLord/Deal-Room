"""add delivery project and assignment models

Revision ID: c36d163f7478
Revises: 1ec640fce501
Create Date: 2026-09-09 13:02:04.513189
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c36d163f7478"
down_revision: Union[str, Sequence[str], None] = "1ec640fce501"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "delivery_projects",
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("poc_id", sa.Integer(), nullable=True),
        sa.Column("project_name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.opportunity_id"],
        ),
        sa.ForeignKeyConstraint(
            ["poc_id"],
            ["poc_tracker.poc_id"],
        ),
        sa.PrimaryKeyConstraint("project_id"),
    )

    op.create_index(
        "ix_delivery_projects_created_by",
        "delivery_projects",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        "ix_delivery_projects_opportunity_id",
        "delivery_projects",
        ["opportunity_id"],
        unique=False,
    )
    op.create_index(
        "ix_delivery_projects_poc_id",
        "delivery_projects",
        ["poc_id"],
        unique=False,
    )
    op.create_index(
        "ix_delivery_projects_status",
        "delivery_projects",
        ["status"],
        unique=False,
    )

    op.create_table(
        "delivery_assignments",
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assigned_by"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["delivery_projects.project_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("assignment_id"),
        sa.UniqueConstraint(
            "project_id",
            "user_id",
            name="uq_delivery_assignment_user",
        ),
    )

    op.create_index(
        "ix_delivery_assignments_assigned_by",
        "delivery_assignments",
        ["assigned_by"],
        unique=False,
    )
    op.create_index(
        "ix_delivery_assignments_is_active",
        "delivery_assignments",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_delivery_assignments_project_id",
        "delivery_assignments",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_delivery_assignments_user_id",
        "delivery_assignments",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_delivery_assignments_user_id",
        table_name="delivery_assignments",
    )
    op.drop_index(
        "ix_delivery_assignments_project_id",
        table_name="delivery_assignments",
    )
    op.drop_index(
        "ix_delivery_assignments_is_active",
        table_name="delivery_assignments",
    )
    op.drop_index(
        "ix_delivery_assignments_assigned_by",
        table_name="delivery_assignments",
    )
    op.drop_table("delivery_assignments")

    op.drop_index(
        "ix_delivery_projects_status",
        table_name="delivery_projects",
    )
    op.drop_index(
        "ix_delivery_projects_poc_id",
        table_name="delivery_projects",
    )
    op.drop_index(
        "ix_delivery_projects_opportunity_id",
        table_name="delivery_projects",
    )
    op.drop_index(
        "ix_delivery_projects_created_by",
        table_name="delivery_projects",
    )
    op.drop_table("delivery_projects")
