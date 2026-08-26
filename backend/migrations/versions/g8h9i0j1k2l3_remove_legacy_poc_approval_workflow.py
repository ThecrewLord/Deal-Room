"""Remove legacy POC approval/access-link workflow.

Revision ID: g8h9i0j1k2l3
Revises: f7a8b9c0d1e2
"""
from alembic import op
import sqlalchemy as sa

revision = "g8h9i0j1k2l3"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("poc_tracker"):
        # Existing records from the removed approval workflow remain usable.
        op.execute(sa.text(
            "UPDATE poc_tracker SET status = 'Draft' "
            "WHERE status IN ('Pending Approval', 'Approved', 'Rejected')"
        ))

        columns = {c["name"] for c in sa.inspect(bind).get_columns("poc_tracker")}
        removable = {
            "poc_access_link",
            "stakeholder_signoff",
            "approved_by",
            "approved_at",
            "rejection_reason",
        }
        existing = removable.intersection(columns)

        if existing:
            with op.batch_alter_table("poc_tracker") as batch:
                for name in sorted(existing):
                    batch.drop_column(name)


def downgrade():
    # The removed approval/access workflow is intentionally not restored.
    pass
