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
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
            KeepTogether,
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
            topMargin=20 * mm,
            bottomMargin=18 * mm,
            title=f"POC Report - {poc.poc_name or 'Unnamed POC'}",
            author="Deal Room",
        )

        styles = getSampleStyleSheet()

        # ---------- Styles ----------

        brand_style = ParagraphStyle(
            "Brand",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#374151"),
        )

        title_style = ParagraphStyle(
            "POCTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        )

        subtitle_style = ParagraphStyle(
            "POCSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#6B7280"),
            spaceAfter=14,
        )

        section_style = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#111827"),
            spaceBefore=10,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#374151"),
            spaceAfter=4,
        )

        label_style = ParagraphStyle(
            "Label",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#6B7280"),
        )

        value_style = ParagraphStyle(
            "Value",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#111827"),
        )

        status_style = ParagraphStyle(
            "Status",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1D4ED8"),
            alignment=TA_CENTER,
        )

        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#9CA3AF"),
            alignment=TA_CENTER,
        )

        # ---------- Data ----------

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

        status = poc.status or "N/A"
        target_date = (
            poc.target_date.strftime("%d %b %Y")
            if poc.target_date
            else "N/A"
        )

        generated_date = datetime.now().strftime("%d %b %Y, %I:%M %p")

        def safe_text(value):
            text = str(value or "—")
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")

        # ---------- Story ----------

        story = []

        # Header
        header_table = Table(
            [
                [
                    Paragraph("DEAL ROOM", brand_style),
                    Paragraph(
                        f"Generated {generated_date}",
                        ParagraphStyle(
                            "Generated",
                            parent=footer_style,
                            alignment=TA_LEFT,
                        ),
                    ),
                ]
            ],
            colWidths=[85 * mm, 77 * mm],
        )

        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ])
        )

        story.append(header_table)
        story.append(Spacer(1, 12))

        story.append(
            Paragraph("PROOF OF CONCEPT REPORT", title_style)
        )

        story.append(
            Paragraph(
                safe_text(poc.poc_name or "Unnamed POC"),
                subtitle_style,
            )
        )

        # Summary card
        summary_data = [
            [
                Paragraph("OPPORTUNITY", label_style),
                Paragraph("ACCOUNT", label_style),
                Paragraph("STATUS", label_style),
                Paragraph("TARGET DATE", label_style),
            ],
            [
                Paragraph(safe_text(opportunity_name), value_style),
                Paragraph(safe_text(account_name), value_style),
                Paragraph(safe_text(status), status_style),
                Paragraph(target_date, value_style),
            ],
        ]

        summary_table = Table(
            summary_data,
            colWidths=[47 * mm, 47 * mm, 32 * mm, 36 * mm],
            rowHeights=[8 * mm, 17 * mm],
        )

        summary_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#E5E7EB")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )

        story.append(summary_table)
        story.append(Spacer(1, 8))

        # POC ID
        poc_id_table = Table(
            [
                [
                    Paragraph(
                        f"<b>POC ID:</b> POC-{poc.poc_id}",
                        value_style,
                    )
                ]
            ],
            colWidths=[162 * mm],
        )

        poc_id_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )

        story.append(poc_id_table)

        # Section helper
        def add_section(title, value):
            content = [
                Paragraph(title, section_style),
                Table(
                    [[Paragraph(safe_text(value), body_style)]],
                    colWidths=[162 * mm],
                    style=TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E5E7EB")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                    ]),
                ),
            ]

            story.extend(content)

        add_section("1. Objective", poc.objective)

        # Success + Exit criteria side by side
        story.append(Paragraph("2. Success & Exit Criteria", section_style))

        criteria_table = Table(
            [
                [
                    Paragraph("<b>SUCCESS CRITERIA</b>", label_style),
                    Paragraph("<b>EXIT CRITERIA</b>", label_style),
                ],
                [
                    Paragraph(safe_text(poc.success_metric), body_style),
                    Paragraph(safe_text(poc.exit_criteria), body_style),
                ],
            ],
            colWidths=[80 * mm, 82 * mm],
        )

        criteria_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F9FAFB")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E5E7EB")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ])
        )

        story.append(criteria_table)

        add_section("3. Failure Condition", poc.failure_condition)

        # Outcome
        story.append(Paragraph("4. Outcome", section_style))

        outcome = poc.outcome or "—"

        outcome_table = Table(
            [
                [
                    Paragraph(
                        safe_text(outcome).upper(),
                        status_style,
                    ),
                    Paragraph(
                        safe_text(poc.outcome_notes),
                        body_style,
                    ),
                ]
            ],
            colWidths=[38 * mm, 124 * mm],
        )

        outcome_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#EFF6FF")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F9FAFB")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E5E7EB")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ])
        )

        story.append(outcome_table)

        add_section("5. Execution Remarks", poc.remarks)

        story.append(Spacer(1, 16))

        # Footer
        footer_table = Table(
            [
                [
                    Paragraph(
                        "Deal Room · Proof of Concept Report",
                        footer_style,
                    )
                ],
                [
                    Paragraph(
                        "Confidential · Generated automatically",
                        footer_style,
                    )
                ],
            ],
            colWidths=[162 * mm],
        )

        footer_table.setStyle(
            TableStyle([
                ("LINEABOVE", (0, 0), (-1, 0), 0.7, colors.HexColor("#E5E7EB")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
        )

        story.append(footer_table)

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
