"""Add stakeholder tags for Phase B2.

Revision ID: h9i0j1k2l3m4
Revises: g8h9i0j1k2l3
"""
from alembic import op
import sqlalchemy as sa


revision = "h9i0j1k2l3m4"
down_revision = "g8h9i0j1k2l3"
branch_labels = None
depends_on = None


STAKEHOLDER_TAGS = (
    "Economic Buyer",
    "Technical Champion",
    "End User",
    "Blocker",
    "Decision Maker",
)


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("stakeholder_tags"):
        op.create_table(
            "stakeholder_tags",
            sa.Column(
                "stakeholder_tag_id",
                sa.Integer(),
                primary_key=True,
            ),
            sa.Column(
                "stakeholder_id",
                sa.Integer(),
                nullable=False,
            ),
            sa.Column(
                "opportunity_id",
                sa.Integer(),
                nullable=False,
            ),
            sa.Column(
                "tag",
                sa.String(length=50),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["stakeholder_id"],
                ["stakeholders.stakeholder_id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["opportunity_id"],
                ["opportunities.opportunity_id"],
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint(
                "stakeholder_id",
                "tag",
                name="uq_stakeholder_tag",
            ),
            sa.CheckConstraint(
                "tag IN ("
                "'Economic Buyer', "
                "'Technical Champion', "
                "'End User', "
                "'Blocker', "
                "'Decision Maker'"
                ")",
                name="ck_stakeholder_tag_valid",
            ),
        )

    # Index used for stakeholder tag lookups.
    indexes = {
        index["name"]
        for index in sa.inspect(bind).get_indexes("stakeholder_tags")
    }

    if "ix_stakeholder_tags_stakeholder_id" not in indexes:
        op.create_index(
            "ix_stakeholder_tags_stakeholder_id",
            "stakeholder_tags",
            ["stakeholder_id"],
            unique=False,
        )

    if "ix_stakeholder_tags_opportunity_id" not in indexes:
        op.create_index(
            "ix_stakeholder_tags_opportunity_id",
            "stakeholder_tags",
            ["opportunity_id"],
            unique=False,
        )

    # Database-level enforcement:
    # an opportunity can have at most one Decision Maker.
    indexes = {
        index["name"]
        for index in sa.inspect(bind).get_indexes("stakeholder_tags")
    }

    if "uq_opportunity_decision_maker" not in indexes:
        op.create_index(
            "uq_opportunity_decision_maker",
            "stakeholder_tags",
            ["opportunity_id"],
            unique=True,
            postgresql_where=sa.text("tag = 'Decision Maker'"),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("stakeholder_tags"):
        indexes = {
            index["name"]
            for index in inspector.get_indexes("stakeholder_tags")
        }

        if "uq_opportunity_decision_maker" in indexes:
            op.drop_index(
                "uq_opportunity_decision_maker",
                table_name="stakeholder_tags",
            )

        if "ix_stakeholder_tags_opportunity_id" in indexes:
            op.drop_index(
                "ix_stakeholder_tags_opportunity_id",
                table_name="stakeholder_tags",
            )

        if "ix_stakeholder_tags_stakeholder_id" in indexes:
            op.drop_index(
                "ix_stakeholder_tags_stakeholder_id",
                table_name="stakeholder_tags",
            )

        op.drop_table("stakeholder_tags")
