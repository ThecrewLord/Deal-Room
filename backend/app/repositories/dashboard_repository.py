from sqlalchemy import func
from datetime import datetime, timedelta

from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.stage_master import StageMaster


class DashboardRepository:

    @staticmethod
    def get_total_opportunities():
        return Opportunity.query.count()


    @staticmethod
    def get_total_pipeline_value():

        value = (
            Opportunity.query
            .with_entities(
                func.sum(Opportunity.estimated_value)
            )
            .scalar()
        )

        return float(value or 0)


    @staticmethod
    def get_weighted_forecast():

        opportunities = Opportunity.query.all()

        forecast = 0

        for opp in opportunities:

            forecast += (
                float(opp.estimated_value or 0)
                *
                (opp.probability or 0)
                /
                100
            )

        return round(forecast, 2)


    @staticmethod
    def get_open_opportunities():

        return Opportunity.query.filter_by(
            status="Open"
        ).count()


    @staticmethod
    def get_closed_won():

        return (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_won == True
            )
            .count()
        )


    @staticmethod
    def get_closed_lost():

        return (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_closed == True,
                StageMaster.is_won == False
            )
            .count()
        )


    @staticmethod
    def get_conversion_rate():

        total_closed = (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_closed == True
            )
            .count()
        )

        won = (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_won == True
            )
            .count()
        )

        if total_closed == 0:
            return 0

        return round(
            (won / total_closed) * 100,
            2
        )


    @staticmethod
    def get_stage_ageing():

        opportunities = Opportunity.query.all()

        result = []

        for opp in opportunities:

            if opp.created_at:

                age = (
                    datetime.utcnow()
                    -
                    opp.created_at
                ).days

                result.append(
                    {
                        "opportunity_id": opp.opportunity_id,
                        "age_days": age
                    }
                )

        return result


    @staticmethod
    def get_stalled_deals():

        limit_date = (
            datetime.utcnow()
            -
            timedelta(days=14)
        )

        return (
            Opportunity.query
            .filter(
                Opportunity.status == "Open",
                Opportunity.updated_at < limit_date
            )
            .count()
        )


    @staticmethod
    def get_active_pocs():

        return (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.requires_poc == True,
                Opportunity.status == "Open"
            )
            .count()
        )


    @staticmethod
    def get_win_loss_ratio():

        won = (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_won == True
            )
            .count()
        )

        lost = (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_closed == True,
                StageMaster.is_won == False
            )
            .count()
        )

        if lost == 0:
            return won

        return round(
            won / lost,
            2
        )


    @staticmethod
    def get_partner_contribution():

        if hasattr(
            Opportunity,
            "partner_id"
        ):

            return (
                Opportunity.query
                .filter(
                    Opportunity.partner_id.isnot(None)
                )
                .count()
            )

        return 0