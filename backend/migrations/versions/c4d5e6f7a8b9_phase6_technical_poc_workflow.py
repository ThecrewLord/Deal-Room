"""phase 6 technical solution and POC workflow

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-08-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("solution_designs"):
        op.create_table(
            "solution_designs",
            sa.Column("design_id", sa.Integer(), primary_key=True),
            sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.opportunity_id"), nullable=False),
            sa.Column("solution_summary", sa.Text(), nullable=True),
            sa.Column("technical_approach", sa.Text(), nullable=True),
            sa.Column("technical_requirements", sa.Text(), nullable=True),
            sa.Column("architecture_notes", sa.Text(), nullable=True),
            sa.Column("risks", sa.Text(), nullable=True),
            sa.Column("assumptions", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("opportunity_id", name="uq_solution_design_opportunity"),
        )

    if inspector.has_table("poc_tracker"):
        columns = {c["name"] for c in sa.inspect(bind).get_columns("poc_tracker")}
        additions = {
            "exit_criteria": sa.Column("exit_criteria", sa.Text(), nullable=True),
            "poc_access_link": sa.Column("poc_access_link", sa.Text(), nullable=True),
            "requested_by": sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=True),
            "approved_by": sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=True),
            "approved_at": sa.Column("approved_at", sa.DateTime(), nullable=True),
            "rejection_reason": sa.Column("rejection_reason", sa.Text(), nullable=True),
            "submitted_by": sa.Column("submitted_by", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=True),
            "submitted_at": sa.Column("submitted_at", sa.DateTime(), nullable=True),
        }
        for name, column in additions.items():
            if name not in columns:
                op.add_column("poc_tracker", column)
        indexes = {i["name"] for i in sa.inspect(bind).get_indexes("poc_tracker")}
        for name, col in (
            ("ix_poc_tracker_status", "status"),
            ("ix_poc_tracker_requested_by", "requested_by"),
            ("ix_poc_tracker_approved_by", "approved_by"),
            ("ix_poc_tracker_submitted_by", "submitted_by"),
        ):
            if name not in indexes:
                op.create_index(name, "poc_tracker", [col], unique=False)

    # Existing records are deliberately not backfilled: NULL means the
    # historical record predates the Phase 6 field and its original data is preserved.
    # Existing status values are not silently rewritten.


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("poc_tracker"):
        indexes = {i["name"] for i in sa.inspect(bind).get_indexes("poc_tracker")}
        for name in (
            "ix_poc_tracker_submitted_by",
            "ix_poc_tracker_approved_by",
            "ix_poc_tracker_requested_by",
            "ix_poc_tracker_status",
        ):
            if name in indexes:
                op.drop_index(name, table_name="poc_tracker")
        columns = {c["name"] for c in sa.inspect(bind).get_columns("poc_tracker")}
        for name in (
            "submitted_at", "submitted_by", "rejection_reason",
            "approved_at", "approved_by", "requested_by",
            "poc_access_link", "exit_criteria",
        ):
            if name in columns:
                op.drop_column("poc_tracker", name)
    if inspector.has_table("solution_designs"):
        indexes = {i["name"] for i in sa.inspect(bind).get_indexes("solution_designs")}
        if "ix_solution_designs_opportunity_id" in indexes:
            op.drop_index("ix_solution_designs_opportunity_id", table_name="solution_designs")
        op.drop_table("solution_designs")
