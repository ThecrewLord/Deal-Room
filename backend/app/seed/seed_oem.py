from app.database import db
from app.models.account.oem_partner import OEMPartner


def seed_oem():

    if OEMPartner.query.first():
        return

    partners = [

        OEMPartner(
            account_id=1,
            partner_name="JFrog",
            product_name="JFrog Platform",
            contact_person="Partner Team",
            email="partner@jfrog.com",
            status="Active",
        ),

        OEMPartner(
            account_id=1,
            partner_name="IBM",
            product_name="IBM Instana",
            contact_person="Partner Team",
            email="partner@ibm.com",
            status="Active",
        ),

        OEMPartner(
            account_id=2,
            partner_name="MeshIQ",
            product_name="MeshIQ Observe",
            contact_person="Partner Team",
            email="partner@meshiq.com",
            status="Active",
        ),

    ]

    db.session.add_all(partners)
    db.session.commit()