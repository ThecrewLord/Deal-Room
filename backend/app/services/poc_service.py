from datetime import datetime, date
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam

from sqlalchemy.exc import IntegrityError

from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.roles import PRE_SALES_MANAGER, SOLUTION_ENGINEER
from app.constants.activity_types import (
    POC_REQUESTED,
    POC_EXECUTION_STARTED, POC_RESULT_SUBMITTED, POC_COMPLETED,
    POC_DESIGN_CREATED, POC_DESIGN_UPDATED,
)
from app.database import db
from app.models.auth.user import User
from app.models.opportunity.poc_tracker import POCTracker
from app.repositories.poc_repository import PocRepository
from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService
from app.utils.concurrency import ConcurrencyManager
from app.constants.poc_outcome import (POC_STATUS_DRAFT, POC_STATUS_IN_PROGRESS, POC_STATUS_SUBMITTED, POC_STATUS_COMPLETED)


class PocService:
    @staticmethod
    def get_by_id(poc_id, user, active_role):
        poc = PocRepository.get_by_id(poc_id)
        if not AuthorizationService.can_view_poc(user, active_role, poc):
            return None
        return poc

    @staticmethod
    def get_by_opportunity(opportunity_id, user, active_role):
        opportunity = PocRepository.get_opportunity(opportunity_id)
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return []
        return PocRepository.get_by_opportunity(opportunity_id)

    @staticmethod
    def generate_poc_pdf(poc_id, user, active_role):
        from io import BytesIO

        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        poc = PocRepository.get_by_id(poc_id)

        if not poc:
            return None

        if not AuthorizationService.can_view_poc(
            user,
            active_role,
            poc,
        ):
            raise AuthorizationDenied(
                "You are not authorized to download this POC."
            )

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "POCTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=20,
            spaceAfter=12,
        )

        heading_style = ParagraphStyle(
            "POCHeading",
            parent=styles["Heading2"],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "POCBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
        )

        story = []

        story.append(
            Paragraph("Proof of Concept Report", title_style)
        )

        story.append(
            Paragraph(
                poc.poc_name or "Unnamed POC",
                styles["Heading1"],
            )
        )

        opportunity = getattr(poc, "opportunity", None)

        opportunity_name = (
            opportunity.opportunity_name
            if opportunity
            else "N/A"
        )

        account_name = (
            opportunity.account.account_name
            if opportunity and opportunity.account
            else "N/A"
        )

        summary_data = [
            ["Opportunity", opportunity_name],
            ["Account", account_name],
            ["POC Status", poc.status or "N/A"],
            ["Target Date", str(poc.target_date or "N/A")],
        ]

        summary_table = Table(
            summary_data,
            colWidths=[42 * mm, 120 * mm],
        )

        summary_table.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, "grey"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ])
        )

        story.append(summary_table)

        sections = [
            ("Objective", poc.objective),
            ("Success Criteria", poc.success_metric),
            ("Exit Criteria", poc.exit_criteria),
            ("Failure Condition", poc.failure_condition),
            ("Outcome", poc.outcome),
            ("Outcome Notes", poc.outcome_notes),
            ("Execution Remarks", poc.remarks),
        ]

        for heading, value in sections:
            story.append(
                Paragraph(heading, heading_style)
            )
            story.append(
                Paragraph(
                    str(value or "—").replace("\n", "<br/>"),
                    body_style,
                )
            )

        story.append(Spacer(1, 12))

        story.append(
            Paragraph(
                "Generated by Deal Room",
                body_style,
            )
        )

        document.build(story)

        buffer.seek(0)

        return buffer

    @staticmethod
    def request_poc(data, user, active_role):
        opportunity = PocRepository.get_opportunity(data["opportunity_id"])
        print(
            "POC DEBUG:",
            "user_id=", getattr(user, "user_id", None),
            "user_name=", getattr(user, "full_name", None),
            "active_role=", active_role,
            "opportunity_id=", data.get("opportunity_id"),
        )        

        if not opportunity:
            return None
        if not AuthorizationService.can_request_poc(user, active_role, opportunity):
            raise AuthorizationDenied("Only an assigned Solution Engineer can request a POC.")
        required = ("objective", "success_metric", "exit_criteria", "target_date", "failure_condition")
        if any(not data.get(field) for field in required):
            raise ValueError("Objective, Success Criteria, Exit Criteria, Target Date and Failure Condition are required.")
        if data["target_date"] < date.today():
            raise ValueError("Target Date cannot be in the past.")

        payload = dict(data)
        payload["status"] = POC_STATUS_DRAFT
        payload["requested_by"] = user.user_id
        poc = PocRepository.create(payload)
        ActivityService.log(
            "POC", poc.poc_id, POC_REQUESTED,
            f"POC '{poc.poc_name}' requested by {user.full_name}.",
            user.user_id, commit=False,
        )
        ActivityService.log(
            "POC", poc.poc_id, POC_DESIGN_CREATED,
            f"POC design '{poc.poc_name}' created with the request.",
            user.user_id, commit=False,
        )
        db.session.commit()
        return poc

    @staticmethod
    def update_design(poc_id, data, user, active_role):
        poc = PocRepository.get_by_id(poc_id)
        if not poc:
            return None
        if not AuthorizationService.can_edit_poc_design(user, active_role, poc):
            raise AuthorizationDenied("Only the assigned Solution Engineer can edit a draft POC design.")
        if ConcurrencyManager.has_conflict(data.get("updated_at"), poc.updated_at):
            raise RuntimeError("This POC changed since you opened it. Refresh before editing.")
        data = dict(data)
        data.pop("updated_at", None)
        if poc.status != POC_STATUS_DRAFT:
            raise RuntimeError("Only a draft POC can be edited.")
        for key, value in data.items():
            if key in {"poc_name", "objective", "success_metric", "exit_criteria", "target_date", "failure_condition", "remarks"}:
                setattr(poc, key, value)
        ActivityService.log(
            "POC", poc.poc_id, POC_DESIGN_UPDATED,
            f"POC design '{poc.poc_name}' updated.",
            user.user_id, commit=False,
        )
        db.session.commit()
        return poc

    @staticmethod
    def start_execution(poc_id, updated_at, user, active_role):
        poc = PocRepository.get_by_id(poc_id)
        if not poc:
            return None
        if not AuthorizationService.can_execute_poc(user, active_role, poc):
            raise AuthorizationDenied("Only an assigned Solution Engineer can execute a draft POC.")
        if poc.status != POC_STATUS_DRAFT:
            raise RuntimeError("Only a draft POC can start execution.")
        if ConcurrencyManager.has_conflict(updated_at, poc.updated_at):
            raise RuntimeError("This POC changed since you opened it. Refresh before starting execution.")
        poc.status = POC_STATUS_IN_PROGRESS
        poc.start_date = poc.start_date or date.today()
        ActivityService.log(
            "POC", poc.poc_id, POC_EXECUTION_STARTED,
            f"POC '{poc.poc_name}' execution started by {user.full_name}.",
            user.user_id, commit=False,
        )
        db.session.commit()
        return poc

    @staticmethod
    def get_eligible_opportunities(user, active_role):
        if active_role != SOLUTION_ENGINEER:
            return []

        opportunities = (
            Opportunity.query
            .join(
                OpportunityTeam,
                OpportunityTeam.opportunity_id == Opportunity.opportunity_id,
            )
            .filter(
                OpportunityTeam.user_id == user.user_id,
                OpportunityTeam.role == SOLUTION_ENGINEER,
                Opportunity.is_active.is_(True),
            )
            .all()
        )

        return [
            opportunity
            for opportunity in opportunities
            if (
                opportunity.current_stage
                and (
                    opportunity.current_stage.stage_name == "POC / Technical Evaluation"
                )
                and not POCTracker.query.filter_by(
                    opportunity_id=opportunity.opportunity_id
                ).first()
            )
        ]

    @staticmethod
    def submit_result(poc_id, data, user, active_role):
        poc = PocRepository.get_by_id(poc_id)
        if not poc:
            return None
        if not AuthorizationService.can_execute_poc(user, active_role, poc):
            raise AuthorizationDenied("Only an assigned Solution Engineer can submit the POC result.")
        if poc.status != POC_STATUS_IN_PROGRESS:
            raise RuntimeError("POC must be In Progress before a result can be submitted.")
        if data.get("execution_status") != POC_STATUS_SUBMITTED:
            raise ValueError("Execution status must be Submitted when submitting a POC result.")
        if ConcurrencyManager.has_conflict(data.get("updated_at"), poc.updated_at):
            raise RuntimeError("This POC changed since you opened it. Refresh before submitting.")
        poc.status = POC_STATUS_SUBMITTED
        poc.outcome = data["outcome"]
        poc.outcome_notes = data["outcome_notes"]
        poc.remarks = data.get("remarks")
        poc.submitted_by = user.user_id
        poc.submitted_at = datetime.utcnow()
        poc.end_date = date.today()
        ActivityService.log(
            "POC", poc.poc_id, POC_RESULT_SUBMITTED,
            f"POC '{poc.poc_name}' result submitted by {user.full_name}.",
            user.user_id, commit=False,
        )
        for member in poc.opportunity.team_members:
            if member.role == SOLUTION_ENGINEER:
                NotificationService.queue(
                    member.user_id, POC_RESULT_SUBMITTED, "POC", poc.poc_id,
                    f"POC '{poc.poc_name}' result is ready for your technical review.",
                )
        db.session.commit()
        return poc

    @staticmethod
    def complete_poc(poc_id, updated_at, user, active_role):
        poc = PocRepository.get_by_id(poc_id)
        if not poc:
            return None
        if not AuthorizationService.can_complete_poc(user, active_role, poc):
            raise AuthorizationDenied("Only an assigned Solution Engineer can complete a submitted POC.")
        if ConcurrencyManager.has_conflict(updated_at, poc.updated_at):
            raise RuntimeError("This POC changed since you opened it. Refresh before completing.")
        poc.status = POC_STATUS_COMPLETED
        ActivityService.log(
            "POC", poc.poc_id, POC_COMPLETED,
            f"POC '{poc.poc_name}' marked Completed after Solution Engineer review.",
            user.user_id, commit=False,
        )
        db.session.commit()
        return poc

    @staticmethod
    def delete_poc(poc_id, user, active_role):
        poc = PocRepository.get_by_id(poc_id)
        if not poc:
            return False
        raise AuthorizationDenied("POCs are immutable business records and cannot be deleted.")
