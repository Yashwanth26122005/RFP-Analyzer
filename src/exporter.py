import io
from typing import List, Dict
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

def export_excel(data: Dict[str, List[Dict]]) -> bytes:
    """Export multiple sheets of data to Excel bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sheet_name, rows in data.items():
            if rows:
                df = pd.DataFrame(rows)
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return buf.getvalue()

def export_pdf_report(
    summary: str,
    requirements: List[Dict],
    security: List[Dict],
    compliance: List[Dict],
    risks: List[Dict],
    clarifications: List[Dict],
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    def h1(text):
        story.append(Paragraph(text, styles["h1"]))
        story.append(Spacer(1, 0.3*cm))

    def h2(text):
        story.append(Paragraph(text, styles["h2"]))
        story.append(Spacer(1, 0.2*cm))

    def body(text):
        story.append(Paragraph(text.replace("\n", "<br/>"), styles["Normal"]))
        story.append(Spacer(1, 0.3*cm))

    def table_section(title, rows, cols):
        if not rows:
            return
        h2(title)
        data = [cols] + [[str(r.get(k, "")) for k in [c.lower().replace(" ", "_") for c in cols]] for r in rows]
        t = Table(data, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4057")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

    h1("RFP Analysis Report")
    h2("Executive Summary")
    body(summary or "Not generated.")

    table_section("Requirements", requirements, ["Category", "Requirement", "Page"])
    table_section("Security Findings", security, ["Category", "Requirement", "Page"])
    table_section("Compliance Findings", compliance, ["Standard", "Requirement", "Page"])
    table_section("Risk Analysis", risks, ["Category", "Description", "Severity"])
    table_section("Clarification Questions", clarifications, ["Group", "Question"])

    doc.build(story)
    return buf.getvalue()
