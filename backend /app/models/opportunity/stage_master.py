from app.database import db
from app.models.base import BaseModel


class StageMaster(BaseModel):
    __tablename__ = "stage_master"

    stage_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    stage_name = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    display_order = db.Column(
        db.Integer,
        nullable=False,
    )

    requires_poc = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    is_closed = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    is_won = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    opportunities = db.relationship(
        "Opportunity",
        back_populates="current_stage",
        lazy=True,
    )

    # Keep only if StageHistory still exists in your project
    stage_history = db.relationship(
        "StageHistory",
        back_populates="stage",
        lazy=True,
    )

    def __repr__(self):
        return (
            f"<StageMaster(stage_id={self.stage_id}, "
            f"stage_name='{self.stage_name}')>"
        )