from app.database import db
from app.models.base import BaseModel


class OEMPartner(BaseModel):
    __tablename__ = "oem_partners"

    oem_partner_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    account_id = db.Column(
        db.Integer,
        db.ForeignKey("accounts.account_id"),
        nullable=False,
        index=True,
    )

    partner_name = db.Column(
        db.String(150),
        nullable=False,
    )

    product_name = db.Column(
        db.String(150),
        nullable=False,
    )

    contact_person = db.Column(
        db.String(150),
    )

    email = db.Column(
        db.String(150),
    )

    phone = db.Column(
        db.String(50),
    )

    status = db.Column(
        db.String(50),
        default="Active",
        nullable=False,
    )

    notes = db.Column(
        db.Text,
    )

    account = db.relationship(
        "Account",
        back_populates="oem_partners",
    )

    def __repr__(self):
        return f"<OEMPartner {self.partner_name}>"