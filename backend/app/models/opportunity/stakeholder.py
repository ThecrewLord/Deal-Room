from sqlalchemy import CheckConstraint, Index

from app.database import db
from app.models.base import BaseModel


STAKEHOLDER_TAGS = (
    "Economic Buyer",
    "Technical Champion",
    "End User",
    "Blocker",
    "Decision Maker",
)


class Stakeholder(BaseModel):
    __tablename__ = "stakeholders"

    stakeholder_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id"),
        nullable=False,
        index=True,
    )

    stakeholder_name = db.Column(
        db.String(150),
        nullable=False,
    )

    designation = db.Column(
        db.String(150),
    )

    email = db.Column(
        db.String(150),
    )

    phone = db.Column(
        db.String(50),
    )

    influence_level = db.Column(
        db.String(50),
    )

    notes = db.Column(
        db.Text,
    )

    opportunity = db.relationship(
        "Opportunity",
        back_populates="stakeholders",
    )

    tags = db.relationship(
        "StakeholderTag",
        back_populates="stakeholder",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def tag_names(self):
        return sorted(tag.tag for tag in self.tags)

    def has_tag(self, tag_name):
        return any(tag.tag == tag_name for tag in self.tags)

    def __repr__(self):
        return f"<Stakeholder {self.stakeholder_name}>"


class StakeholderTag(BaseModel):
    __tablename__ = "stakeholder_tags"

    stakeholder_tag_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    stakeholder_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "stakeholders.stakeholder_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Kept on the tag record so PostgreSQL can enforce
    # one Decision Maker per opportunity.
    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "opportunities.opportunity_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    tag = db.Column(
        db.String(50),
        nullable=False,
    )

    stakeholder = db.relationship(
        "Stakeholder",
        back_populates="tags",
    )

    opportunity = db.relationship(
        "Opportunity",
        back_populates="stakeholder_tags",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "stakeholder_id",
            "tag",
            name="uq_stakeholder_tag",
        ),

        db.CheckConstraint(
            "tag IN ("
            "'Economic Buyer', "
            "'Technical Champion', "
            "'End User', "
            "'Blocker', "
            "'Decision Maker'"
            ")",
            name="ck_stakeholder_tag_valid",
        ),

        # Database-level enforcement:
        # only one Decision Maker can exist for an opportunity.
        Index(
            "uq_opportunity_decision_maker",
            "opportunity_id",
            unique=True,
            postgresql_where=db.text(
                "tag = 'Decision Maker'"
            ),
            sqlite_where=db.text(
                "tag = 'Decision Maker'"
            ),
        ),
    )

    def __repr__(self):
        return f"<StakeholderTag {self.tag}>"
