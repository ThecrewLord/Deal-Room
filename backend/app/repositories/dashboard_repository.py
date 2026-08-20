from datetime import datetime, timedelta

from sqlalchemy import func

from app.database import db

from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.stage_master import StageMaster
from app.models.opportunity.poc_tracker import POCTracker
from app.models.system.audit_log import AuditLog
from app.models.auth.user import User


class DashboardRepository:

    @staticmethod
    def get_total_opportunities():
        return Opportunity.query.count()

    @staticmethod
    def get_total_pipeline_value():
        value = (
            Opportunity.query
            .filter(
                Opportunity.status == "Open",
                Opportunity.is_active == True,
            )
            .with_entities(
                func.sum(Opportunity.estimated_value)
            )
            .scalar()
        )

        return float(value or 0)

    @staticmethod
    def get_weighted_forecast():
        opportunities = (
            Opportunity.query
            .filter(
                Opportunity.status == "Open",
                Opportunity.is_active == True,
            )
            .all()
        )

        forecast = 0

        for opportunity in opportunities:
            forecast += (
                float(
                    opportunity.estimated_value or 0
                )
                *
                (opportunity.probability or 0)
                /
                100
            )

        return round(forecast, 2)

    @staticmethod
    def get_open_opportunities():
        return (
            Opportunity.query
            .filter(
                Opportunity.status == "Open",
                Opportunity.is_active == True,
            )
            .count()
        )

    @staticmethod
    def get_closed_won():
        return (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_won == True,
                Opportunity.is_active == True,
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
                StageMaster.is_won == False,
                Opportunity.is_active == True,
            )
            .count()
        )

    @staticmethod
    def get_conversion_rate():
        total_closed = (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_closed == True,
                Opportunity.is_active == True,
            )
            .count()
        )

        won = (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_won == True,
                Opportunity.is_active == True,
            )
            .count()
        )

        if total_closed == 0:
            return 0

        return round(
            (won / total_closed) * 100,
            2,
        )

    @staticmethod
    def get_stage_ageing():
        opportunities = (
            Opportunity.query
            .filter(
                Opportunity.is_active == True,
            )
            .all()
        )

        result = []

        for opportunity in opportunities:
            if opportunity.created_at:
                age = (
                    datetime.utcnow()
                    -
                    opportunity.created_at
                ).days

                result.append(
                    {
                        "opportunity_id":
                            opportunity.opportunity_id,
                        "age_days": age,
                    }
                )

        return result

    @staticmethod
    def get_average_stage_ageing():
        opportunities = (
            Opportunity.query
            .filter(
                Opportunity.is_active == True,
            )
            .all()
        )

        if not opportunities:
            return 0

        ages = []

        for opportunity in opportunities:
            if opportunity.created_at:
                ages.append(
                    (
                        datetime.utcnow()
                        -
                        opportunity.created_at
                    ).days
                )

        if not ages:
            return 0

        return round(
            sum(ages) / len(ages),
            1,
        )

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
                Opportunity.is_active == True,
                Opportunity.updated_at < limit_date,
            )
            .count()
        )

    @staticmethod
    def get_active_pocs():
        return (
            POCTracker.query
            .filter(
                POCTracker.status.in_(
                    ["Active", "In Progress"]
                )
            )
            .count()
        )

    @staticmethod
    def get_win_loss_ratio():
        won = (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_won == True,
                Opportunity.is_active == True,
            )
            .count()
        )

        lost = (
            Opportunity.query
            .join(StageMaster)
            .filter(
                StageMaster.is_closed == True,
                StageMaster.is_won == False,
                Opportunity.is_active == True,
            )
            .count()
        )

        if lost == 0:
            return won

        return round(
            won / lost,
            2,
        )

    @staticmethod
    def get_partner_contribution():
        if hasattr(Opportunity, "partner_id"):
            return (
                Opportunity.query
                .filter(
                    Opportunity.partner_id.isnot(None)
                )
                .count()
            )

        return 0

    # ==========================================================
    # PHASE 3 DASHBOARD DATA
    # ==========================================================

    @staticmethod
    def get_pipeline_by_stage():

        rows = (
            db.session.query(
                StageMaster.stage_name,
                func.count(
                    Opportunity.opportunity_id
                ),
                func.coalesce(
                    func.sum(
                        Opportunity.estimated_value
                    ),
                    0,
                ),
            )
            .join(
                Opportunity,
                Opportunity.stage_id ==
                StageMaster.stage_id,
            )
            .filter(
                Opportunity.is_active == True,
            )
            .group_by(
                StageMaster.stage_id,
                StageMaster.stage_name,
                StageMaster.display_order,
            )
            .order_by(
                StageMaster.display_order.asc()
            )
            .all()
        )

        return [
            {
                "stage": row[0],
                "count": row[1],
                "value": float(row[2] or 0),
            }
            for row in rows
        ]

    @staticmethod
    def get_recent_opportunities(limit=5):

        opportunities = (
            Opportunity.query
            .filter(
                Opportunity.is_active == True,
            )
            .order_by(
                Opportunity.updated_at.desc()
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "id": opportunity.opportunity_id,
                "name": opportunity.opportunity_name,
                "account": (
                    opportunity.account.account_name
                    if opportunity.account
                    else "-"
                ),
                "stage": (
                    opportunity.current_stage.stage_name
                    if opportunity.current_stage
                    else "-"
                ),
                "value": float(
                    opportunity.estimated_value or 0
                ),
                "probability":
                    opportunity.probability or 0,
                "status":
                    opportunity.status,
                "updated_at":
                    opportunity.updated_at,
            }
            for opportunity in opportunities
        ]

    @staticmethod
    def get_upcoming_pocs(limit=5):

        today = datetime.utcnow().date()

        pocs = (
            POCTracker.query
            .filter(
                POCTracker.target_date >= today,
            )
            .order_by(
                POCTracker.target_date.asc()
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "id": poc.poc_id,
                "opportunity": (
                    poc.opportunity.opportunity_name
                    if poc.opportunity
                    else "-"
                ),
                "objective":
                    poc.objective,
                "target_date":
                    poc.target_date,
                "status":
                    poc.status,
                "stakeholder_signoff":
                    (
                        "Signed"
                        if poc.stakeholder_signoff
                        else "Pending sign-off"
                    ),
            }
            for poc in pocs
        ]

    @staticmethod
    def get_recent_activity(limit=6):

        logs = (
            AuditLog.query
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        result = []

        for log in logs:

            user_name = "System"

            if log.performed_by:
                user = (
                    User.query
                    .filter_by(
                        user_id=log.performed_by
                    )
                    .first()
                )

                if user:
                    user_name = user.full_name

            result.append(
                {
                    "id":
                        log.audit_log_id,
                    "user":
                        user_name,
                    "action":
                        log.action,
                    "entity_type":
                        log.entity_type,
                    "entity_id":
                        log.entity_id,
                    "details":
                        log.description or "",
                    "timestamp":
                        log.created_at,
                }
            )

        return result