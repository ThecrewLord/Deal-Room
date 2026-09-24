from datetime import datetime
from app.database import db

class OEMOpportunity(db.Model):
    __tablename__ = "opportunity_oems"
    opportunity_oem_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.opportunity_id", ondelete="RESTRICT"), nullable=False, index=True)
    oem_partner_id = db.Column(db.Integer, db.ForeignKey("oem_partners.oem_partner_id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    opportunity = db.relationship("Opportunity", back_populates="oem_associations")
    oem = db.relationship("OEMPartner", back_populates="opportunity_associations")
    creator = db.relationship("User", foreign_keys=[created_by])

class RFXContext(db.Model):
    __tablename__ = "rfx_contexts"
    rfx_context_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.opportunity_id", ondelete="RESTRICT"), nullable=False, unique=True)
    drive_link = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    opportunity = db.relationship("Opportunity", back_populates="rfx_context")

class NegotiationContext(db.Model):
    __tablename__ = "negotiation_contexts"
    negotiation_context_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.opportunity_id", ondelete="RESTRICT"), nullable=False, unique=True)
    nda_suggested = db.Column(db.Boolean, nullable=False, default=False)
    nda_link = db.Column(db.Text)
    msa_link = db.Column(db.Text)
    sow_link = db.Column(db.Text)
    notes = db.Column(db.Text)
    row_version = db.Column(db.Integer, nullable=False, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    opportunity = db.relationship("Opportunity", back_populates="negotiation_context")

class POCTeamMember(db.Model):
    __tablename__ = "poc_team_members"
    poc_team_member_id = db.Column(db.Integer, primary_key=True)
    poc_id = db.Column(db.Integer, db.ForeignKey("poc_tracker.poc_id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    role = db.Column(db.String(30), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", foreign_keys=[user_id])
    assigner = db.relationship("User", foreign_keys=[assigned_by])

class DeliveryProject(db.Model):
    __tablename__ = "delivery_projects"
    delivery_project_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.opportunity_id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.account_id", ondelete="RESTRICT"), nullable=False, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Active")
    completed_at = db.Column(db.DateTime)
    row_version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    opportunity = db.relationship("Opportunity", back_populates="delivery_project")
    account = db.relationship("Account")
    manager = db.relationship("User", foreign_keys=[manager_id])
    members = db.relationship("DeliveryProjectMember", back_populates="project", cascade="all, delete-orphan", lazy=True)

class DeliveryProjectMember(db.Model):
    __tablename__ = "delivery_project_members"
    delivery_project_member_id = db.Column(db.Integer, primary_key=True)
    delivery_project_id = db.Column(db.Integer, db.ForeignKey("delivery_projects.delivery_project_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    is_done = db.Column(db.Boolean, nullable=False, default=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    project = db.relationship("DeliveryProject", back_populates="members")
    user = db.relationship("User", foreign_keys=[user_id])
    assigner = db.relationship("User", foreign_keys=[assigned_by])

class Activity(db.Model):
    __tablename__ = "activities"
    activity_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.opportunity_id", ondelete="RESTRICT"), nullable=False, index=True)
    activity_type = db.Column(db.String(30), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    follow_up_id = db.Column(db.Integer, db.ForeignKey("follow_ups.follow_up_id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actor = db.relationship("User", foreign_keys=[actor_id])
    opportunity = db.relationship("Opportunity", back_populates="activities")

class FollowUp(db.Model):
    __tablename__ = "follow_ups"
    follow_up_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.opportunity_id", ondelete="RESTRICT"), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Open")
    completed_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    opportunity = db.relationship("Opportunity", back_populates="follow_ups")
    owner = db.relationship("User", foreign_keys=[owner_id])
    creator = db.relationship("User", foreign_keys=[created_by])
