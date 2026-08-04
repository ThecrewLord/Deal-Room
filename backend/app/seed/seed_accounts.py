from app.database import db
from app.models.account.account import Account


def seed_accounts():

    if Account.query.first():
        return

    accounts = [

        Account(
            account_name="Dataeko Enterprise",
            industry="Technology",
            website="https://dataeko.ai",
            is_active=True
        ),

        Account(
            account_name="JFrog",
            industry="DevSecOps",
            website="https://jfrog.com",
            is_active=True
        ),

    ]

    db.session.add_all(accounts)
    db.session.commit()