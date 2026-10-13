"""A5: Closed Won request/approval workflow.

Revision ID: n5o6p7q8r9s0
Revises: m4n5o6p7q8r9
"""
from alembic import op
import sqlalchemy as sa

revision = "n5o6p7q8r9s0"
down_revision = "m4n5o6p7q8r9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "closed_won_requests",
        sa.Column("request_id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=False),
        sa.Column("requested_active_role", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Pending"),
        sa.Column("resolved_by", sa.Integer(), nullable=True),
        sa.Column("resolved_active_role", sa.String(length=100), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.opportunity_id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.user_id"]),
        sa.UniqueConstraint("opportunity_id", name="uq_closed_won_requests_opportunity"),
        sa.CheckConstraint(
            "status IN ('Pending', 'Approved', 'Rejected')",
            name="ck_closed_won_requests_status",
        ),
    )
    op.create_index(
        "ix_closed_won_requests_opportunity_id",
        "closed_won_requests",
        ["opportunity_id"],
    )
    op.create_index(
        "ix_closed_won_requests_status",
        "closed_won_requests",
        ["status"],
    )


def downgrade():
    op.drop_index("ix_closed_won_requests_status", table_name="closed_won_requests")
    op.drop_index("ix_closed_won_requests_opportunity_id", table_name="closed_won_requests")
    op.drop_table("closed_won_requests")
