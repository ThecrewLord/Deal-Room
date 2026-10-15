"""P1 POC closure history and one-open-POC integrity.

Revision ID: c6d7e8f9a0b1
Revises: b4c5d6e7f8a9
"""
from alembic import op
import sqlalchemy as sa

revision = "c6d7e8f9a0b1"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    duplicates = bind.execute(sa.text(
        "SELECT opportunity_id, COUNT(*) AS n FROM poc_tracker "
        "WHERE status IN ('Draft','In Progress','Submitted') "
        "GROUP BY opportunity_id HAVING COUNT(*) > 1"
    )).fetchall()
    if duplicates:
        raise RuntimeError(
            "Cannot add one-open-POC constraint: duplicate unresolved POCs exist "
            f"for opportunity IDs {[row[0] for row in duplicates]}. Resolve them explicitly before retrying."
        )
    op.create_index(
        "uq_poc_tracker_one_open_per_opportunity",
        "poc_tracker",
        ["opportunity_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('Draft','In Progress','Submitted')"),
        sqlite_where=sa.text("status IN ('Draft','In Progress','Submitted')"),
    )
    with op.batch_alter_table("poc_history") as batch_op:
        batch_op.drop_constraint("ck_poc_history_event_type", type_="check")
        batch_op.create_check_constraint(
            "ck_poc_history_event_type",
            "event_type IN ('POC_STARTED','POC_SUBMITTED','POC_COMPLETED','NEW_POC_REQUESTED')",
        )


def downgrade():
    op.drop_index("uq_poc_tracker_one_open_per_opportunity", table_name="poc_tracker")
    with op.batch_alter_table("poc_history") as batch_op:
        batch_op.drop_constraint("ck_poc_history_event_type", type_="check")
        batch_op.create_check_constraint(
            "ck_poc_history_event_type",
            "event_type IN ('POC_STARTED','POC_SUBMITTED','NEW_POC_REQUESTED')",
        )
