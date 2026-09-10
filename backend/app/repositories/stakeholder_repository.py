from app.database import db
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.stakeholder import Stakeholder, StakeholderTag


class StakeholderRepository:
    @staticmethod
    def create(data):
        stakeholder = Stakeholder(**data)
        db.session.add(stakeholder)
        return stakeholder

    @staticmethod
    def get_by_id(stakeholder_id):
        return Stakeholder.query.get(stakeholder_id)

    @staticmethod
    def get_opportunity(opportunity_id):
        return Opportunity.query.get(opportunity_id)

    @staticmethod
    def get_by_opportunity(opportunity_id):
        return Stakeholder.query.filter_by(opportunity_id=opportunity_id).all()

    @staticmethod
    def get_tag_by_id(stakeholder_tag_id):
        return StakeholderTag.query.get(stakeholder_tag_id)

    @staticmethod
    def get_tags(stakeholder_id):
        return (
            StakeholderTag.query
            .filter_by(stakeholder_id=stakeholder_id)
            .order_by(StakeholderTag.tag.asc())
            .all()
        )

    @staticmethod
    def get_decision_maker(opportunity_id):
        return (
            StakeholderTag.query
            .filter_by(
                opportunity_id=opportunity_id,
                tag="Decision Maker",
            )
            .first()
        )

    @staticmethod
    def create_tag(stakeholder_id, opportunity_id, tag):
        stakeholder_tag = StakeholderTag(
            stakeholder_id=stakeholder_id,
            opportunity_id=opportunity_id,
            tag=tag,
        )
        db.session.add(stakeholder_tag)
        return stakeholder_tag

    @staticmethod
    def delete_tag(stakeholder_tag):
        db.session.delete(stakeholder_tag)
        db.session.commit()
        return True

    @staticmethod
    def update(stakeholder, data):
        for key, value in data.items():
            setattr(stakeholder, key, value)
        return stakeholder

    @staticmethod
    def delete(stakeholder):
        db.session.delete(stakeholder)
        db.session.commit()
        return True
