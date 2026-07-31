from app.database import db
from app.models.base import BaseModel


class Account(BaseModel):
    __tablename__ = "accounts"

    account_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    account_name = db.Column(
        db.String(200),
        nullable=False,
        unique=True,
        index=True,
    )

    industry = db.Column(
        db.String(100),
    )

    website = db.Column(
        db.String(255),
    )

    phone = db.Column(
        db.String(50),
    )

    country = db.Column(
        db.String(100),
    )

    state = db.Column(
        db.String(100),
    )

    city = db.Column(
        db.String(100),
    )

    address = db.Column(
        db.Text,
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )

    contacts = db.relationship(
        "Contact",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy=True,
    )

    opportunities = db.relationship(
        "Opportunity",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy=True,
    )

    oem_partners = db.relationship(
        "OEMPartner",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<Account {self.account_name}>"