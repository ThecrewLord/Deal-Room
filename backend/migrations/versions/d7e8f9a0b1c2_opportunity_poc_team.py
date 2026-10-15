"""Create canonical opportunity-level POC team memberships.

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
"""
from alembic import op
import sqlalchemy as sa

revision = "d7e8f9a0b1c2"
down_revision = "c6d7e8f9a0b1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "opportunity_poc_team_members",
        sa.Column("opportunity_poc_team_member_id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.opportunity_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("opportunity_id", "user_id", name="uq_opportunity_poc_team_member_user"),
        sa.CheckConstraint("role IN ('DevOps Engineer', 'Data Analyst')", name="ck_opportunity_poc_team_role"),
    )
    op.create_index("ix_opportunity_poc_team_members_opportunity_id", "opportunity_poc_team_members", ["opportunity_id"])
    op.create_index("ix_opportunity_poc_team_members_user_id", "opportunity_poc_team_members", ["user_id"])

    # Backfill from the earliest POC cycle for each opportunity. Existing cycle
    # memberships remain intact as execution snapshots for backward compatibility.
    bind = op.get_bind()
    bind.execute(sa.text("""
        INSERT INTO opportunity_poc_team_members
            (opportunity_id, user_id, role, assigned_by, assigned_at)
        SELECT p.opportunity_id, tm.user_id, tm.role, tm.assigned_by, tm.assigned_at
        FROM poc_team_members tm
        JOIN poc_tracker p ON p.poc_id = tm.poc_id
        WHERE p.poc_id = (
            SELECT MIN(p2.poc_id) FROM poc_tracker p2
            JOIN poc_team_members tm2 ON tm2.poc_id = p2.poc_id
            WHERE p2.opportunity_id = p.opportunity_id
        )
    """))


def downgrade():
    op.drop_index("ix_opportunity_poc_team_members_user_id", table_name="opportunity_poc_team_members")
    op.drop_index("ix_opportunity_poc_team_members_opportunity_id", table_name="opportunity_poc_team_members")
    op.drop_table("opportunity_poc_team_members")
