"""Phase 2 V2 business domains and collaboration workflows."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
revision="p2a3b4c5d6e7"
down_revision="f7a8b9c0d1e2"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    insp=sa.inspect(bind)
    # Accounts: canonical identity + explicit lifecycle status.
    cols={c["name"] for c in insp.get_columns("accounts")}
    if "canonical_name" not in cols: op.add_column("accounts",sa.Column("canonical_name",sa.String(200),nullable=True))
    if "status" not in cols: op.add_column("accounts",sa.Column("status",sa.String(20),nullable=True))
    bind.execute(text("UPDATE accounts SET canonical_name=lower(regexp_replace(trim(account_name), '\\s+', ' ', 'g')) WHERE canonical_name IS NULL"))
    bind.execute(text("UPDATE accounts SET status=CASE WHEN is_active THEN 'Active' ELSE 'Archived' END WHERE status IS NULL"))
    op.alter_column("accounts","canonical_name",nullable=False,existing_type=sa.String(200))
    op.alter_column("accounts","status",nullable=False,existing_type=sa.String(20))
    # Remove legacy uniqueness on display name; canonical identity is authoritative.
    for uc in insp.get_unique_constraints("accounts"):
        if uc.get("column_names")==["account_name"] and uc.get("name"):
            op.drop_constraint(uc["name"], "accounts", type_="unique")
    for ix in insp.get_indexes("accounts"):
        if ix.get("unique") and ix.get("column_names")==["account_name"]:
            op.drop_index(ix["name"],table_name="accounts")
    if "uq_accounts_canonical_name" not in {x["name"] for x in insp.get_indexes("accounts")}:
        op.create_index("uq_accounts_canonical_name","accounts",["canonical_name"],unique=True)

    # Stakeholders: V2 identity/tag model.
    cols={c["name"] for c in insp.get_columns("stakeholders")}
    if "name" not in cols:
        op.alter_column("stakeholders","stakeholder_name",new_column_name="name")
    if "job_title" not in cols:
        op.alter_column("stakeholders","designation",new_column_name="job_title")
    cols={c["name"] for c in insp.get_columns("stakeholders")}
    if "company" not in cols: op.add_column("stakeholders",sa.Column("company",sa.String(200),nullable=True))
    if "is_decision_maker" not in cols: op.add_column("stakeholders",sa.Column("is_decision_maker",sa.Boolean(),nullable=False,server_default=sa.false()))
    # The old influence value is not a V2 source of truth; only preserve Decision Maker semantics.
    bind.execute(text("UPDATE stakeholders SET is_decision_maker=TRUE WHERE lower(coalesce(influence_level,''))='decision maker'"))
    op.execute("CREATE TABLE IF NOT EXISTS stakeholder_tag_links (stakeholder_id INTEGER NOT NULL REFERENCES stakeholders(stakeholder_id) ON DELETE CASCADE, tag_id INTEGER NOT NULL REFERENCES tags(tag_id) ON DELETE RESTRICT, PRIMARY KEY(stakeholder_id,tag_id))")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_stakeholder_decision_maker_per_opportunity ON stakeholders(opportunity_id) WHERE is_decision_maker = TRUE")
    if "influence_level" in {c["name"] for c in insp.get_columns("stakeholders")}:
        op.drop_column("stakeholders","influence_level")
    tags=["Economic Buyer","Technical Champion","End User","Blocker","Decision Maker"]
    for t in tags:
        bind.execute(text("INSERT INTO tags(name,is_active,created_at,updated_at) SELECT :n,TRUE,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP WHERE NOT EXISTS(SELECT 1 FROM tags WHERE name=:n)"),{"n":t})

    # POC authoritative extension on poc_tracker; old poc table is disposable and is no longer imported.
    cols={c["name"] for c in insp.get_columns("poc_tracker")}
    additions=[("input_drive_link",sa.Text()),("result_view_link",sa.Text()),("submission_metadata",sa.JSON())]
    for n,t in additions:
        if n not in cols: op.add_column("poc_tracker",sa.Column(n,t,nullable=True))
    # The old duplicate POC aggregate is disposable development data. Keep only
    # poc_tracker as the authoritative V2 POC aggregate.
    op.execute("DROP TABLE IF EXISTS poc")
    op.execute("CREATE TABLE IF NOT EXISTS poc_team_members (poc_team_member_id SERIAL PRIMARY KEY, poc_id INTEGER NOT NULL REFERENCES poc_tracker(poc_id) ON DELETE RESTRICT, user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT, role VARCHAR(30) NOT NULL CHECK(role IN ('DevOps Engineer','Data Analyst')), assigned_by INTEGER NOT NULL REFERENCES users(user_id), assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(poc_id,user_id,role))")

    op.execute("CREATE TABLE IF NOT EXISTS opportunity_oems (opportunity_oem_id SERIAL PRIMARY KEY, opportunity_id INTEGER NOT NULL REFERENCES opportunities(opportunity_id) ON DELETE RESTRICT, oem_partner_id INTEGER NOT NULL REFERENCES oem_partners(oem_partner_id) ON DELETE RESTRICT, created_by INTEGER NOT NULL REFERENCES users(user_id), created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(opportunity_id,oem_partner_id))")
    op.execute("CREATE INDEX IF NOT EXISTS ix_opportunity_oems_opportunity_id ON opportunity_oems(opportunity_id)")

    op.execute("CREATE TABLE IF NOT EXISTS rfx_contexts (rfx_context_id SERIAL PRIMARY KEY, opportunity_id INTEGER NOT NULL UNIQUE REFERENCES opportunities(opportunity_id) ON DELETE RESTRICT, drive_link TEXT, created_by INTEGER NOT NULL REFERENCES users(user_id), updated_by INTEGER REFERENCES users(user_id), created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    op.execute("CREATE TABLE IF NOT EXISTS negotiation_contexts (negotiation_context_id SERIAL PRIMARY KEY, opportunity_id INTEGER NOT NULL UNIQUE REFERENCES opportunities(opportunity_id) ON DELETE RESTRICT, nda_suggested BOOLEAN NOT NULL DEFAULT FALSE, nda_link TEXT, msa_link TEXT, sow_link TEXT, notes TEXT, row_version INTEGER NOT NULL DEFAULT 1, created_by INTEGER NOT NULL REFERENCES users(user_id), updated_by INTEGER REFERENCES users(user_id), created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)")

    op.execute("CREATE TABLE IF NOT EXISTS delivery_projects (delivery_project_id SERIAL PRIMARY KEY, opportunity_id INTEGER NOT NULL UNIQUE REFERENCES opportunities(opportunity_id) ON DELETE RESTRICT, account_id INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE RESTRICT, manager_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT, status VARCHAR(20) NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Done')), completed_at TIMESTAMP, row_version INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    op.execute("CREATE TABLE IF NOT EXISTS delivery_project_members (delivery_project_member_id SERIAL PRIMARY KEY, delivery_project_id INTEGER NOT NULL REFERENCES delivery_projects(delivery_project_id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT, is_done BOOLEAN NOT NULL DEFAULT FALSE, assigned_by INTEGER NOT NULL REFERENCES users(user_id), assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TIMESTAMP, UNIQUE(delivery_project_id,user_id))")

    op.execute("CREATE TABLE IF NOT EXISTS activities (activity_id SERIAL PRIMARY KEY, opportunity_id INTEGER NOT NULL REFERENCES opportunities(opportunity_id) ON DELETE RESTRICT, activity_type VARCHAR(30) NOT NULL CHECK(activity_type IN ('call','meeting','email','note','interaction')), summary TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT, follow_up_id INTEGER NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_activities_opportunity_id ON activities(opportunity_id)")
    op.execute("CREATE TABLE IF NOT EXISTS follow_ups (follow_up_id SERIAL PRIMARY KEY, opportunity_id INTEGER NOT NULL REFERENCES opportunities(opportunity_id) ON DELETE RESTRICT, owner_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT, description TEXT NOT NULL, due_date DATE NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'Open' CHECK(status IN ('Open','Completed','Overdue')), completed_at TIMESTAMP, created_by INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    op.execute("ALTER TABLE activities ADD CONSTRAINT fk_activity_follow_up FOREIGN KEY(follow_up_id) REFERENCES follow_ups(follow_up_id) ON DELETE SET NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_follow_ups_opportunity_id ON follow_ups(opportunity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_follow_ups_owner_id ON follow_ups(owner_id)")

def downgrade():
    raise RuntimeError("Phase 2 migration is intentionally one-way for V2 development safety.")
