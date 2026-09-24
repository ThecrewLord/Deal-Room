"""add immutable POC business history

Revision ID: 9b5c7d1e2f34
Revises: 8a4b6c7d9e01
Create Date: 2026-09-24
"""
from alembic import op
import sqlalchemy as sa

revision = "9b5c7d1e2f34"
down_revision = "8a4b6c7d9e01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "poc_history",
        sa.Column("history_id", sa.Integer(), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('POC_STARTED','POC_SUBMITTED','NEW_POC_REQUESTED')",
            name="ck_poc_history_event_type",
        ),
        sa.CheckConstraint(
            "event_type <> 'NEW_POC_REQUESTED' OR "
            "(reason IS NOT NULL AND length(trim(reason)) > 0)",
            name="ck_poc_history_repeat_reason",
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.opportunity_id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.user_id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("history_id"),
    )
    op.create_index(
        "ix_poc_history_opportunity_created_at",
        "poc_history",
        ["opportunity_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_poc_history_actor_id", "poc_history", ["actor_id"], unique=False
    )

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("""
            CREATE OR REPLACE FUNCTION prevent_poc_history_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'poc_history is append-only';
            END;
            $$ LANGUAGE plpgsql;
        """))
        op.execute(sa.text("""
            CREATE TRIGGER trg_poc_history_immutable
            BEFORE UPDATE OR DELETE ON poc_history
            FOR EACH ROW EXECUTE FUNCTION prevent_poc_history_mutation();
        """))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text(
            "DROP TRIGGER IF EXISTS trg_poc_history_immutable ON poc_history"
        ))
        op.execute(sa.text(
            "DROP FUNCTION IF EXISTS prevent_poc_history_mutation()"
        ))
    op.drop_index("ix_poc_history_actor_id", table_name="poc_history")
    op.drop_index(
        "ix_poc_history_opportunity_created_at",
        table_name="poc_history",
    )
    op.drop_table("poc_history")
