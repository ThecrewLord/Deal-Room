"""A3: add pain points to opportunities.

Revision ID: k2l3m4n5o6p7
Revises: j1k2l3m4n5o6
"""
from alembic import op
import sqlalchemy as sa

revision = "k2l3m4n5o6p7"
down_revision = "j1k2l3m4n5o6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("opportunities", sa.Column("pain_points", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("opportunities", "pain_points")
