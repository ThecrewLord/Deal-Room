"""phase 5 pre-sales technical team assignment

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("opportunity_team"):
        raise RuntimeError("Phase 5 requires the existing opportunity_team table from Phase 3.")

    # Technical assignment is final and duplicate (opportunity, user, role)
    # rows must never be possible. Do not silently delete historical data if
    # an existing database already violates this invariant; fail the migration
    # and require explicit data review instead.
    duplicate = bind.execute(
        sa.text(
            """
            SELECT opportunity_id, user_id, role, COUNT(*) AS duplicate_count
            FROM opportunity_team
            GROUP BY opportunity_id, user_id, role
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if duplicate:
        raise RuntimeError(
            "Phase 5 migration stopped because duplicate OpportunityTeam rows exist "
            f"for opportunity_id={duplicate[0]}, user_id={duplicate[1]}, role={duplicate[2]}. "
            "Resolve duplicates explicitly before rerunning the migration."
        )

    indexes = {index["name"] for index in inspector.get_indexes("opportunity_team")}
    unique_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("opportunity_team")}
    if "uq_opportunity_team_member_role" not in indexes and "uq_opportunity_team_member_role" not in unique_constraints:
        op.create_index(
            "uq_opportunity_team_member_role",
            "opportunity_team",
            ["opportunity_id", "user_id", "role"],
            unique=True,
        )

    opportunity_indexes = {index["name"] for index in inspector.get_indexes("opportunities")}
    if "ix_opportunities_status_sales_owner" not in opportunity_indexes:
        op.create_index(
            "ix_opportunities_status_sales_owner",
            "opportunities",
            ["status", "sales_owner_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    opportunity_indexes = {index["name"] for index in inspector.get_indexes("opportunities")}
    if "ix_opportunities_status_sales_owner" in opportunity_indexes:
        op.drop_index("ix_opportunities_status_sales_owner", table_name="opportunities")

    team_indexes = {index["name"] for index in inspector.get_indexes("opportunity_team")}
    if "uq_opportunity_team_member_role" in team_indexes:
        op.drop_index("uq_opportunity_team_member_role", table_name="opportunity_team")
