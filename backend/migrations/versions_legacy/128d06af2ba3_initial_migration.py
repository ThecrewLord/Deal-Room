"""initial migration

Revision ID: 128d06af2ba3
Revises: 
Create Date: 2026-08-03 10:49:11.735905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '128d06af2ba3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table("users",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("manager_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("auth_version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["manager_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table("user_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "role",
            name="uq_user_role",
        ),
    )

    op.create_table("token_blocklist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=255), nullable=False),
        sa.Column("token_type", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti"),
    )

    op.create_table("accounts",
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("account_name", sa.String(length=200), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("account_id"),
        sa.UniqueConstraint("account_name"),
    )

    op.create_table("contacts",
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.account_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("contact_id"),
    )

    op.create_table("tags",
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("tag_id"),
        sa.UniqueConstraint("name"),
    )

    op.create_index(
        "ix_tags_name",
        "tags",
        ["name"],
        unique=False,
    )



    op.create_index(
        "ix_accounts_account_name",
        "accounts",
        ["account_name"],
        unique=False,
    )


    op.create_index(
        "ix_token_blocklist_jti",
        "token_blocklist",
        ["jti"],
        unique=False,
    )

    op.create_index(
        "ix_token_blocklist_user_id",
        "token_blocklist",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_user_roles_user_id",
        "user_roles",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_user_roles_role",
        "user_roles",
        ["role"],
        unique=False,
    )
    op.create_index(
        "ix_users_manager_id",
        "users",
        ["manager_id"],
        unique=False,
    )

    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('audit_logs',
    sa.Column('audit_log_id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('performed_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('audit_log_id')
    )
    op.create_table('oem_partners',
    sa.Column('oem_partner_id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('partner_name', sa.String(length=150), nullable=False),
    sa.Column('product_name', sa.String(length=150), nullable=False),
    sa.Column('contact_person', sa.String(length=150), nullable=True),
    sa.Column('email', sa.String(length=150), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], ),
    sa.PrimaryKeyConstraint('oem_partner_id')
    )
    op.create_index(op.f('ix_oem_partners_account_id'), 'oem_partners', ['account_id'], unique=False)
    # StageMaster is referenced by opportunities, so it must exist before the
    # opportunities table is created on fresh Alembic databases.
    op.create_table('stage_master',
    sa.Column('stage_id', sa.Integer(), nullable=False),
    sa.Column('stage_name', sa.String(length=100), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('requires_poc', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('is_closed', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('is_won', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('stage_id'),
    sa.UniqueConstraint('stage_name', name='uq_stage_master_stage_name')
    )
    op.create_index('ix_stage_master_stage_name', 'stage_master', ['stage_name'], unique=True)
    op.create_table('opportunities',
    sa.Column('opportunity_id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('stage_id', sa.Integer(), nullable=False),
    sa.Column('opportunity_name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('estimated_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('probability', sa.Integer(), nullable=True),
    sa.Column('expected_close_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], ),
    sa.ForeignKeyConstraint(['stage_id'], ['stage_master.stage_id'], ),
    sa.PrimaryKeyConstraint('opportunity_id')
    )
    op.create_index(op.f('ix_opportunities_account_id'), 'opportunities', ['account_id'], unique=False)
    op.create_index(op.f('ix_opportunities_stage_id'), 'opportunities', ['stage_id'], unique=False)
    op.create_table('opportunity_team',
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('opportunity_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.opportunity_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('team_id')
    )
    op.create_index(op.f('ix_opportunity_team_opportunity_id'), 'opportunity_team', ['opportunity_id'], unique=False)
    op.create_index(op.f('ix_opportunity_team_user_id'), 'opportunity_team', ['user_id'], unique=False)
    op.create_table('poc_tracker',
    sa.Column('poc_id', sa.Integer(), nullable=False),
    sa.Column('opportunity_id', sa.Integer(), nullable=False),
    sa.Column('poc_name', sa.String(length=150), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('remarks', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.opportunity_id'], ),
    sa.PrimaryKeyConstraint('poc_id')
    )
    op.create_index(op.f('ix_poc_tracker_opportunity_id'), 'poc_tracker', ['opportunity_id'], unique=False)
    op.create_table('stage_history',
    sa.Column('history_id', sa.Integer(), nullable=False),
    sa.Column('opportunity_id', sa.Integer(), nullable=False),
    sa.Column('stage_id', sa.Integer(), nullable=False),
    sa.Column('changed_by', sa.Integer(), nullable=True),
    sa.Column('remarks', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['changed_by'], ['users.user_id'], ),
    sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.opportunity_id'], ),
    sa.ForeignKeyConstraint(['stage_id'], ['stage_master.stage_id'], ),
    sa.PrimaryKeyConstraint('history_id')
    )
    op.create_index(op.f('ix_stage_history_opportunity_id'), 'stage_history', ['opportunity_id'], unique=False)
    op.create_index(op.f('ix_stage_history_stage_id'), 'stage_history', ['stage_id'], unique=False)
    op.create_table('stakeholders',
    sa.Column('stakeholder_id', sa.Integer(), nullable=False),
    sa.Column('opportunity_id', sa.Integer(), nullable=False),
    sa.Column('stakeholder_name', sa.String(length=150), nullable=False),
    sa.Column('designation', sa.String(length=150), nullable=True),
    sa.Column('email', sa.String(length=150), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('influence_level', sa.String(length=50), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.opportunity_id'], ),
    sa.PrimaryKeyConstraint('stakeholder_id')
    )
    op.create_index(op.f('ix_stakeholders_opportunity_id'), 'stakeholders', ['opportunity_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_stakeholders_opportunity_id'), table_name='stakeholders')
    op.drop_table('stakeholders')
    op.drop_index(op.f('ix_stage_history_stage_id'), table_name='stage_history')
    op.drop_index(op.f('ix_stage_history_opportunity_id'), table_name='stage_history')
    op.drop_table('stage_history')
    op.drop_index(op.f('ix_poc_tracker_opportunity_id'), table_name='poc_tracker')
    op.drop_table('poc_tracker')
    op.drop_index(op.f('ix_opportunity_team_user_id'), table_name='opportunity_team')
    op.drop_index(op.f('ix_opportunity_team_opportunity_id'), table_name='opportunity_team')
    op.drop_table('opportunity_team')
    op.drop_index(op.f('ix_opportunities_stage_id'), table_name='opportunities')
    op.drop_index(op.f('ix_opportunities_account_id'), table_name='opportunities')
    op.drop_table('opportunities')
    op.drop_index('ix_stage_master_stage_name', table_name='stage_master')
    op.drop_table('stage_master')
    op.drop_index(op.f('ix_oem_partners_account_id'), table_name='oem_partners')
    op.drop_table('oem_partners')
    op.drop_table('audit_logs')
    # ### end Alembic commands ###
