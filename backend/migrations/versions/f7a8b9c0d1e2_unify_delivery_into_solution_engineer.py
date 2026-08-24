"""Unify the former Delivery role into Solution Engineer and auto-approve POCs."""

from alembic import op
import sqlalchemy as sa

revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade():
    # Remove legacy Delivery role rows where the same user already has the
    # canonical Solution Engineer role, avoiding the unique constraint.
    op.execute(sa.text(
        "DELETE FROM user_roles "
        "WHERE role = 'Delivery' "
        "AND EXISTS (SELECT 1 FROM user_roles se "
        "WHERE se.user_id = user_roles.user_id AND se.role = 'Solution Engineer')"
    ))
    op.execute(sa.text(
        "UPDATE user_roles SET role = 'Solution Engineer' WHERE role = 'Delivery'"
    ))

    # Existing technical team assignments are also unified. Remove duplicate
    # Delivery assignments for a user who is already assigned as SE.
    op.execute(sa.text(
        "DELETE FROM opportunity_team "
        "WHERE role = 'Delivery' "
        "AND EXISTS (SELECT 1 FROM opportunity_team se "
        "WHERE se.opportunity_id = opportunity_team.opportunity_id "
        "AND se.user_id = opportunity_team.user_id "
        "AND se.role = 'Solution Engineer')"
    ))
    op.execute(sa.text(
        "UPDATE opportunity_team SET role = 'Solution Engineer' WHERE role = 'Delivery'"
    ))

    # POCs that were waiting for manager approval can proceed immediately now.
    op.execute(sa.text(
        "UPDATE poc_tracker SET status = 'Approved', approved_by = NULL, approved_at = NULL "
        "WHERE status = 'Pending Approval'"
    ))


def downgrade():
    # The business model intentionally does not support restoring Delivery as
    # a distinct role. A downgrade therefore leaves canonical data untouched.
    pass
