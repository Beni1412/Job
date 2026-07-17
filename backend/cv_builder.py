"""
CV Builder — Generates a clean AWS/Amazon-style resume PDF using ReportLab
"""
import io
from typing import List, Dict, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ─── Color Palette (AWS-inspired clean style) ────────────────────────────────
DARK_GREEN   = colors.HexColor("#013e37")
BUTTER       = colors.HexColor("#ffefb3")
BLACK        = colors.HexColor("#111111")
DARK_GRAY    = colors.HexColor("#333333")
MID_GRAY     = colors.HexColor("#555555")
LIGHT_GRAY   = colors.HexColor("#888888")
RULE_COLOR   = colors.HexColor("#013e37")

PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm


def build_resume_pdf(profile: dict, skills: list, experience: list, education: list) -> bytes:
    """
    Build a professional resume PDF and return as bytes.
    
    Args:
        profile: dict with keys: full_name, email, phone, address, city, linkedin, github, about_me
        skills: list of dicts with: skill_name, category
        experience: list of dicts with: company, title, start_date, end_date, is_current, description
        education: list of dicts with: institution, degree, field, grad_year, gpa
    
    Returns:
        PDF file as bytes
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    # ─── Styles ──────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    style_name = ParagraphStyle(
        "Name",
        fontSize=22,
        fontName="Helvetica-Bold",
        textColor=DARK_GREEN,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    style_contact = ParagraphStyle(
        "Contact",
        fontSize=8.5,
        fontName="Helvetica",
        textColor=MID_GRAY,
        spaceAfter=1,
        alignment=TA_LEFT,
    )
    style_section_title = ParagraphStyle(
        "SectionTitle",
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=DARK_GREEN,
        spaceBefore=10,
        spaceAfter=3,
        leading=14,
        alignment=TA_LEFT,
    )
    style_body = ParagraphStyle(
        "Body",
        fontSize=9,
        fontName="Helvetica",
        textColor=DARK_GRAY,
        spaceAfter=3,
        leading=13,
        alignment=TA_LEFT,
    )
    style_job_title = ParagraphStyle(
        "JobTitle",
        fontSize=9.5,
        fontName="Helvetica-Bold",
        textColor=BLACK,
        spaceAfter=1,
        leading=13,
    )
    style_company = ParagraphStyle(
        "Company",
        fontSize=9,
        fontName="Helvetica-Oblique",
        textColor=MID_GRAY,
        spaceAfter=2,
        leading=12,
    )
    style_skill_tag = ParagraphStyle(
        "SkillTag",
        fontSize=8.5,
        fontName="Helvetica",
        textColor=DARK_GRAY,
        spaceAfter=2,
    )

    # ─── Build Story ─────────────────────────────────────────────────────────
    story = []

    full_name = profile.get("full_name") or "Your Name"
    email     = profile.get("email", "")
    phone     = profile.get("phone", "")
    city      = profile.get("city", "")
    address   = profile.get("address", "")
    linkedin  = profile.get("linkedin", "")
    github    = profile.get("github", "")
    about_me  = profile.get("about_me", "")

    # ── Name ──
    story.append(Paragraph(full_name, style_name))

    # ── Contact line ──
    contact_parts = []
    if email:    contact_parts.append(email)
    if phone:    contact_parts.append(phone)
    if city:     contact_parts.append(city)
    if address:  contact_parts.append(address)
    if linkedin: contact_parts.append(f"linkedin.com/in/{linkedin.replace('https://linkedin.com/in/','').replace('linkedin.com/in/','')}")
    if github:   contact_parts.append(f"github.com/{github.replace('https://github.com/','').replace('github.com/','')}")

    if contact_parts:
        story.append(Paragraph("  ·  ".join(contact_parts), style_contact))

    story.append(HRFlowable(width="100%", thickness=1.5, color=DARK_GREEN, spaceAfter=6, spaceBefore=4))

    # ── Professional Summary ──
    if about_me and about_me.strip():
        story.append(Paragraph("PROFESSIONAL SUMMARY", style_section_title))
        story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=4))
        story.append(Paragraph(about_me, style_body))

    # ── Skills ──
    if skills:
        story.append(Paragraph("SKILLS", style_section_title))
        story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=4))

        # Group skills by category
        skill_groups: Dict[str, List[str]] = {}
        for sk in skills:
            cat = (sk.get("category") or "Technical").title()
            name = sk.get("skill_name", "")
            if name:
                skill_groups.setdefault(cat, []).append(name)

        cat_order = ["Technical", "Tech", "Tools", "Tool", "Soft"]
        sorted_cats = sorted(
            skill_groups.keys(),
            key=lambda c: cat_order.index(c) if c in cat_order else 99
        )

        for cat in sorted_cats:
            names = skill_groups[cat]
            line = f"<b>{cat}:</b>  {',  '.join(names)}"
            story.append(Paragraph(line, style_skill_tag))
            story.append(Spacer(1, 2))

    # ── Work Experience ──
    if experience:
        story.append(Paragraph("WORK EXPERIENCE", style_section_title))
        story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=4))

        for exp in experience:
            title   = exp.get("title", "")
            company = exp.get("company", "")
            start   = exp.get("start_date", "")
            end     = "Present" if exp.get("is_current") else exp.get("end_date", "")
            desc    = exp.get("description", "")

            date_str = f"{start} – {end}" if start else end

            # Two-column: title + date
            table_data = [[
                Paragraph(title, style_job_title),
                Paragraph(date_str, ParagraphStyle("DateRight", fontSize=8.5,
                    fontName="Helvetica", textColor=LIGHT_GRAY, alignment=TA_RIGHT))
            ]]
            t = Table(table_data, colWidths=[12*cm, 4*cm])
            t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
            story.append(t)
            story.append(Paragraph(company, style_company))

            if desc:
                for bullet in desc.split("\n"):
                    bullet = bullet.strip().lstrip("•-").strip()
                    if bullet:
                        story.append(Paragraph(f"• {bullet}", style_body))

            story.append(Spacer(1, 6))

    # ── Education ──
    if education:
        story.append(Paragraph("EDUCATION", style_section_title))
        story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=4))

        for edu in education:
            institution = edu.get("institution", "")
            degree      = edu.get("degree", "")
            field       = edu.get("field", "")
            grad_year   = edu.get("grad_year", "")
            gpa         = edu.get("gpa", "")

            degree_line = " ".join(filter(None, [degree, f"in {field}" if field else ""]))

            table_data = [[
                Paragraph(institution, style_job_title),
                Paragraph(grad_year or "", ParagraphStyle("DateRight", fontSize=8.5,
                    fontName="Helvetica", textColor=LIGHT_GRAY, alignment=TA_RIGHT))
            ]]
            t = Table(table_data, colWidths=[12*cm, 4*cm])
            t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
            story.append(t)

            if degree_line:
                story.append(Paragraph(degree_line, style_company))
            if gpa:
                story.append(Paragraph(f"GPA: {gpa}", style_body))

            story.append(Spacer(1, 6))

    # ─── Build ───────────────────────────────────────────────────────────────
    doc.build(story)
    buf.seek(0)
    return buf.read()
