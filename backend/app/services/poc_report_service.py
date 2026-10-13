from datetime import datetime

from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.database import db
from app.models.opportunity.poc_tracker import POCTracker


class POCReportService:
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

        poc = db.session.get(POCTracker, poc_id)

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

        # Requirement/document content is maintained in the external RFX Drive workspace.
        add_section("1. POC Result View", poc.result_view_link)

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


