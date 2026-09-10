from app.database import db
from app.models.base import BaseModel


class DeliveryProject(BaseModel):
    __tablename__ = "delivery_projects"

    project_id = db.Column(db.Integer, primary_key=True)

    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id"),
        nullable=False,
        index=True,
    )

    poc_id = db.Column(
        db.Integer,
        db.ForeignKey("poc_tracker.poc_id"),
        nullable=True,
        index=True,
    )

    project_name = db.Column(
        db.String(200),
        nullable=False,
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Pending Assignment",
        index=True,
    )

    start_date = db.Column(db.Date, nullable=True)
    target_date = db.Column(db.Date, nullable=True)

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    opportunity = db.relationship(
        "Opportunity",
        backref=db.backref("delivery_projects", lazy=True),
    )

    poc = db.relationship(
        "POCTracker",
        backref=db.backref("delivery_projects", lazy=True),
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
    )

    assignments = db.relationship(
        "DeliveryAssignment",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy=True,
    )
