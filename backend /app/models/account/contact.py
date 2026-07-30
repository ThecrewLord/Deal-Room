from app.database import db
from app.models.base import BaseModel


class Contact(BaseModel):
    __tablename__ = "contacts"

    contact_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    account_id = db.Column(
        db.Integer,
        db.ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )

    full_name = db.Column(
        db.String(150),
        nullable=False,
    )

    title = db.Column(
        db.String(100),
    )

    email = db.Column(
        db.String(150),
    )

    phone = db.Column(
        db.String(50),
    )

    is_primary = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    account = db.relationship(
        "Account",
        back_populates="contacts",
    )

    def __repr__(self):
        return f"<Contact {self.full_name}>"