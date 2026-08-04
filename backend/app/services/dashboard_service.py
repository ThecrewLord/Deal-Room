from datetime import datetime, timedelta

from app.database import db
from app.models.opportunity.opportunity import Opportunity
from app.models.poc.poc import Poc
from app.models.account.oem_partner import OEMPartner


# 1. Total Opportunities
# Formula: COUNT(active opportunities)

def get_total_opportunities():
    return Opportunity.query.filter_by(
        is_active=True
    ).count()



# 2. Total Pipeline Value
# Formula: SUM(opportunity estimated value)

def get_total_pipeline_value():
    result = db.session.query(
        db.func.sum(Opportunity.estimated_value)
    ).filter(
        Opportunity.is_active == True
    ).scalar()

    return result or 0



# 3. Weighted Forecast
# Formula: SUM(estimated value × probability / 100)

def get_weighted_forecast():

    opportunities = Opportunity.query.filter_by(
        is_active=True
    ).all()

    total = 0

    for opp in opportunities:

        weighted_value = (
            float(opp.estimated_value)
            *
            opp.probability
            /
            100
        )

        total += weighted_value


    return total



# 4. Conversion Rate
# Formula:
# Closed Won /
# (Closed Won + Closed Lost) ×100

def get_conversion_rate():

    won = Opportunity.query.filter_by(
        status="Closed Won"
    ).count()


    lost = Opportunity.query.filter_by(
        status="Closed Lost"
    ).count()


    total = won + lost


    if total == 0:
        return 0


    return (won / total) * 100




# 5. Stage Ageing
# Formula:
# Current Date - Stage Entry Date

def get_stage_ageing():

    opportunities = Opportunity.query.filter_by(
        is_active=True
    ).all()


    ageing = []


    for opp in opportunities:

        if opp.stage_history:

            latest_stage = max(
                opp.stage_history,
                key=lambda x: x.created_at
            )


            days = (
                datetime.utcnow().date()
                -
                latest_stage.created_at.date()
            ).days


            ageing.append({

                "opportunity_id": opp.opportunity_id,

                "opportunity_name": opp.opportunity_name,

                "stage_age_days": days

            })


    return ageing




# 6. Stalled Deal
# Rule:
# No activity for more than 14 days

def get_stalled_deals():

    threshold = datetime.utcnow() - timedelta(days=14)


    stalled = []


    opportunities = Opportunity.query.filter_by(
        is_active=True
    ).all()


    for opp in opportunities:


        if opp.updated_at < threshold:

            stalled.append({

                "opportunity_id": opp.opportunity_id,

                "opportunity_name": opp.opportunity_name,

                "status": "Stalled"

            })


    return stalled




# 7. Active POCs
# Formula:
# Count POCs where outcome is empty

def get_active_pocs():

    return Poc.query.filter(
        Poc.outcome.is_(None)
    ).count()




# 8. Win/Loss Ratio
# Formula:
# Closed Won / Closed Lost

def get_win_loss_ratio():

    won = Opportunity.query.filter_by(
        status="Closed Won"
    ).count()


    lost = Opportunity.query.filter_by(
        status="Closed Lost"
    ).count()


    if lost == 0:
        return won


    return won / lost




# 9. Partner Contribution
# Formula:
# SUM(Opportunity Value linked to OEM Partner)

def get_partner_contribution():


    partners = OEMPartner.query.all()


    contribution = []


    for partner in partners:


        total_value = 0


        if partner.account:

            for opp in partner.account.opportunities:

                total_value += float(
                    opp.estimated_value
                )


        contribution.append({

            "partner_name": partner.partner_name,

            "contribution": total_value

        })


    return contribution