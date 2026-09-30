"""A4: Opportunity Value History and Final Revenue foundation.

Revision ID: m4n5o6p7q8r9
Revises: l3m4n5o6p7q8
"""
from alembic import op
import sqlalchemy as sa

revision = "m4n5o6p7q8r9"
down_revision = "l3m4n5o6p7q8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "opportunities",
        sa.Column("final_revenue", sa.Numeric(precision=15, scale=2), nullable=True),
    )
    op.create_check_constraint("ck_opportunities_final_revenue_non_negative", "opportunities", "final_revenue IS NULL OR final_revenue >= 0")
    op.create_table(
        "opportunity_value_history",
        sa.Column("history_id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("old_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("new_value", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("reason", sa.String(length=2000), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("actor_active_role", sa.String(length=100), nullable=False),
        sa.Column("changed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("opportunity_row_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.opportunity_id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["users.user_id"]),
        sa.CheckConstraint("new_value >= 0", name="ck_opportunity_value_history_new_non_negative"),
        sa.CheckConstraint("old_value IS NULL OR old_value >= 0", name="ck_opportunity_value_history_old_non_negative"),
    )
    op.create_index("ix_opportunity_value_history_opportunity_id", "opportunity_value_history", ["opportunity_id"])
    op.create_index("ix_opportunity_value_history_changed_at", "opportunity_value_history", ["changed_at"])
    op.create_index("ix_opportunity_value_history_actor_id", "opportunity_value_history", ["actor_id"])
    op.create_index("ix_opportunity_value_history_actor_active_role", "opportunity_value_history", ["actor_active_role"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
        CREATE OR REPLACE FUNCTION prevent_opportunity_value_history_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Opportunity value history is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """)
        op.execute("""
        CREATE TRIGGER trg_opportunity_value_history_append_only
        BEFORE UPDATE OR DELETE ON opportunity_value_history
        FOR EACH ROW EXECUTE FUNCTION prevent_opportunity_value_history_mutation();
        """)
        op.execute("""
        CREATE OR REPLACE FUNCTION prevent_final_revenue_mutation()
        RETURNS trigger AS $$
        BEGIN
            IF OLD.final_revenue IS NOT NULL AND NEW.final_revenue IS DISTINCT FROM OLD.final_revenue THEN
                RAISE EXCEPTION 'Final Revenue is immutable once established';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
        op.execute("""
        CREATE TRIGGER trg_opportunities_final_revenue_immutable
        BEFORE UPDATE OF final_revenue ON opportunities
        FOR EACH ROW EXECUTE FUNCTION prevent_final_revenue_mutation();
        """)


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_opportunities_final_revenue_immutable ON opportunities")
        op.execute("DROP FUNCTION IF EXISTS prevent_final_revenue_mutation()")
        op.execute("DROP TRIGGER IF EXISTS trg_opportunity_value_history_append_only ON opportunity_value_history")
        op.execute("DROP FUNCTION IF EXISTS prevent_opportunity_value_history_mutation()")
    op.drop_index("ix_opportunity_value_history_actor_active_role", table_name="opportunity_value_history")
    op.drop_index("ix_opportunity_value_history_actor_id", table_name="opportunity_value_history")
    op.drop_index("ix_opportunity_value_history_changed_at", table_name="opportunity_value_history")
    op.drop_index("ix_opportunity_value_history_opportunity_id", table_name="opportunity_value_history")
    op.drop_table("opportunity_value_history")
    op.drop_constraint("ck_opportunities_final_revenue_non_negative", "opportunities", type_="check")
    op.drop_column("opportunities", "final_revenue")
