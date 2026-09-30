"""phase17 database integrity constraints

Revision ID: 2a5516303b0e
Revises: a1c2d3e4f5g6
Create Date: 2026-09-28 19:50:31.578745

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2a5516303b0e"
down_revision: Union[str, Sequence[str], None] = "a1c2d3e4f5g6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add database-level integrity constraints for Phase 17."""

    op.create_check_constraint(
        "ck_opportunities_outcome",
        "opportunities",
        "outcome IN ('Open', 'Closed Won', 'Closed Lost')",
    )

    op.create_check_constraint(
        "ck_follow_ups_status",
        "follow_ups",
        "status IN ('Open', 'Overdue', 'Completed')",
    )

    op.create_check_constraint(
        "ck_activities_activity_type",
        "activities",
        "activity_type IN ('note', 'call')",
    )

    op.create_check_constraint(
        "ck_poc_team_members_role",
        "poc_team_members",
        "role IN ('DevOps Engineer', 'Data Analyst')",
    )

    op.create_check_constraint(
        "ck_delivery_projects_status",
        "delivery_projects",
        "status IN ('Active', 'Done')",
    )


def downgrade() -> None:
    """Remove Phase 17 database integrity constraints."""

    op.drop_constraint(
        "ck_delivery_projects_status",
        "delivery_projects",
        type_="check",
    )

    op.drop_constraint(
        "ck_poc_team_members_role",
        "poc_team_members",
        type_="check",
    )

    op.drop_constraint(
        "ck_activities_activity_type",
        "activities",
        type_="check",
    )

    op.drop_constraint(
        "ck_follow_ups_status",
        "follow_ups",
        type_="check",
    )

    op.drop_constraint(
        "ck_opportunities_outcome",
        "opportunities",
        type_="check",
    )
