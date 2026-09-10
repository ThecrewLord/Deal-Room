from app.database import db
from app.models.base import BaseModel


class OpportunityOEM(BaseModel):
    __tablename__ = "opportunity_oems"

    opportunity_oem_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "opportunities.opportunity_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    oem_partner_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "oem_partners.oem_partner_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    opportunity = db.relationship(
        "Opportunity",
        back_populates="opportunity_oems",
    )

    oem_partner = db.relationship(
        "OEMPartner",
        back_populates="opportunity_oems",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "opportunity_id",
            "oem_partner_id",
            name="uq_opportunity_oem",
        ),
    )

    def __repr__(self):
        return (
            f"<OpportunityOEM "
            f"opportunity={self.opportunity_id} "
            f"oem={self.oem_partner_id}>"
        )
