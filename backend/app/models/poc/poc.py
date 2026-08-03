from datetime import datetime
from app.database import db


class Poc(db.Model):
    __tablename__ = "poc"

    id = db.Column(db.Integer, primary_key=True)

    opportunity_id = db.Column(
    db.Integer,
    nullable=False,
)

    objective = db.Column(db.Text, nullable=False)
    success_metric = db.Column(db.Text, nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    failure_condition = db.Column(db.Text, nullable=False)
    stakeholder_signoff = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    outcome = db.Column(db.String(20))
    outcome_notes = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "objective": self.objective,
            "success_metric": self.success_metric,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "failure_condition": self.failure_condition,
            "stakeholder_signoff": self.stakeholder_signoff,
            "outcome": self.outcome,
            "outcome_notes": self.outcome_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }