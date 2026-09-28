"""Remove obsolete POC document/content fields.

Revision ID: 8a4b6c7d9e01
Revises: 7f3a2c1d9e10
"""
from alembic import op
import sqlalchemy as sa

revision = "8a4b6c7d9e01"
down_revision = "7f3a2c1d9e10"
branch_labels = None
depends_on = None


def upgrade():
    for column in (
        "objective",
        "success_metric",
        "failure_condition",
        "input_drive_link",
        "exit_criteria",
    ):
        op.drop_column("poc_tracker", column)


def downgrade():
    op.add_column("poc_tracker", sa.Column("objective", sa.Text(), nullable=True))
    op.add_column("poc_tracker", sa.Column("success_metric", sa.Text(), nullable=True))
    op.add_column("poc_tracker", sa.Column("failure_condition", sa.Text(), nullable=True))
    op.add_column("poc_tracker", sa.Column("input_drive_link", sa.Text(), nullable=True))
    op.add_column("poc_tracker", sa.Column("exit_criteria", sa.Text(), nullable=True))
