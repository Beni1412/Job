"""
CV Builder — Clean professional resume matching Beni_Mulyawan_Resume_paper style
"""
import io
from typing import List, Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ─── Colors ──────────────────────────────────────────────────────────────────
BLACK      = colors.HexColor("#111111")
DARK_GRAY  = colors.HexColor("#2d2d2d")
MID_GRAY   = colors.HexColor("#555555")
LIGHT_GRAY = colors.HexColor("#888888")
RULE_COLOR = colors.HexColor("#000000")

PAGE_W, PAGE_H = A4
MARGIN_LR = 1.8 * cm
MARGIN_TB = 1.5 * cm


def _hr(thick=0.8):
    return HRFlowable(
        width="100%", thickness=thick,
        color=RULE_COLOR, spaceAfter=5, spaceBefore=0
    )


def build_resume_pdf(profile: dict, skills: list, experience: list, education: list) -> bytes:
    """
    Build a clean professional resume PDF matching Beni_Mulyawan_Resume_paper.pdf style.

    Args:
        profile  : dict with keys: full_name, title, email, phone, city, linkedin, github, about_me
        skills   : list of dicts with: skill_name, category
        experience: list of dicts with: company, title, start_date, end_date, is_current, description
        education: list of dicts with: institution, degree, field, grad_year, gpa

    Returns:
        PDF as bytes
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN_LR,
        rightMargin=MARGIN_LR,
        topMargin=MARGIN_TB,
        bottomMargin=MARGIN_TB,
    )

    # ─── Style Definitions ────────────────────────────────────────────────────
    s_name = ParagraphStyle(
        "Name", fontSize=20, fontName="Helvetica-Bold",
        textColor=BLACK, spaceAfter=3, alignment=TA_LEFT, leading=24,
    )
    s_tagline = ParagraphStyle(
        "Tagline", fontSize=9.5, fontName="Helvetica",
        textColor=MID_GRAY, spaceAfter=3, alignment=TA_LEFT, leading=13,
    )
    s_contact = ParagraphStyle(
        "Contact", fontSize=8.5, fontName="Helvetica",
        textColor=MID_GRAY, spaceAfter=5, alignment=TA_LEFT, leading=12,
    )
    s_section = ParagraphStyle(
        "Section", fontSize=10, fontName="Helvetica-Bold",
        textColor=BLACK, spaceBefore=10, spaceAfter=3, leading=13, alignment=TA_LEFT,
    )
    s_body = ParagraphStyle(
        "Body", fontSize=9, fontName="Helvetica",
        textColor=DARK_GRAY, spaceAfter=2, leading=13, alignment=TA_LEFT,
    )
    s_bold_body = ParagraphStyle(
        "BoldBody", fontSize=9, fontName="Helvetica-Bold",
        textColor=BLACK, spaceAfter=1, leading=13,
    )
    s_italic = ParagraphStyle(
        "Italic", fontSize=9, fontName="Helvetica-Oblique",
        textColor=MID_GRAY, spaceAfter=2, leading=12,
    )
    s_date = ParagraphStyle(
        "DateRight", fontSize=8.5, fontName="Helvetica",
        textColor=LIGHT_GRAY, alignment=TA_RIGHT, leading=12,
    )
    s_bullet = ParagraphStyle(
        "Bullet", fontSize=9, fontName="Helvetica",
        textColor=DARK_GRAY, spaceAfter=2, leading=13,
        leftIndent=10, firstLineIndent=0,
    )
    s_skill_line = ParagraphStyle(
        "SkillLine", fontSize=9, fontName="Helvetica",
        textColor=DARK_GRAY, spaceAfter=3, leading=13,
    )

    # ─── Helpers ──────────────────────────────────────────────────────────────
    usable_w = PAGE_W - MARGIN_LR * 2

    def section_header(title: str) -> list:
        return [
            Spacer(1, 4),
            Paragraph(title, s_section),
            _hr(0.8),
        ]

    def two_col(left_para, right_para, left_w_cm=13.0):
        right_w = usable_w - left_w_cm * cm
        tbl = Table(
            [[left_para, right_para]],
            colWidths=[left_w_cm * cm, right_w],
        )
        tbl.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ]))
        return tbl

    # ─── Profile values ───────────────────────────────────────────────────────
    full_name = (profile.get("full_name") or "Your Name").upper()
    title_tag = profile.get("title") or profile.get("job_title") or ""
    email     = profile.get("email", "")
    phone     = profile.get("phone", "")
    city      = profile.get("city", "")
    linkedin  = profile.get("linkedin", "")
    github    = profile.get("github", "")
    about_me  = profile.get("about_me", "")

    def short_url(url, prefix):
        if not url:
            return ""
        url = url.strip().rstrip("/")
        for p in [f"https://www.{prefix}", f"https://{prefix}", f"http://{prefix}", prefix]:
            if url.startswith(p):
                url = url[len(p):]
        url = url.lstrip("/")
        return f"{prefix}/{url}" if url else ""

    linkedin_short = short_url(linkedin, "linkedin.com/in")
    github_short   = short_url(github,   "github.com")

    # ─── Story ────────────────────────────────────────────────────────────────
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph(full_name, s_name))

    if title_tag:
        story.append(Paragraph(title_tag, s_tagline))

    contact_parts = [p for p in [email, phone, city, github_short, linkedin_short] if p]
    if contact_parts:
        story.append(Paragraph("  |  ".join(contact_parts), s_contact))

    story.append(_hr(1.5))

    # ── Summary ───────────────────────────────────────────────────────────────
    if about_me and about_me.strip():
        story.extend(section_header("SUMMARY"))
        story.append(Paragraph(about_me.strip(), s_body))

    # ── Education ─────────────────────────────────────────────────────────────
    if education:
        story.extend(section_header("EDUCATION"))
        for edu in education:
            institution = edu.get("institution", "")
            degree      = edu.get("degree", "")
            field       = edu.get("field", "")
            grad_year   = edu.get("grad_year", "")
            gpa         = edu.get("gpa", "")
            degree_str  = " ".join(filter(None, [degree, f"in {field}" if field else ""]))

            blk = []
            blk.append(two_col(
                Paragraph(institution, s_bold_body),
                Paragraph(grad_year or "", s_date),
            ))
            if degree_str:
                blk.append(Paragraph(degree_str, s_italic))
            if gpa:
                blk.append(Paragraph(f"GPA: {gpa}", s_body))
            blk.append(Spacer(1, 4))
            story.append(KeepTogether(blk))

    # ── Skills ────────────────────────────────────────────────────────────────
    if skills:
        story.extend(section_header("SKILLS"))

        skill_groups: Dict[str, List[str]] = {}
        for sk in skills:
            cat  = (sk.get("category") or "Technical").strip()
            name = (sk.get("skill_name") or "").strip()
            if name:
                skill_groups.setdefault(cat, []).append(name)

        order = [
            "Programming Languages", "Technical",
            "Machine Learning", "AI", "Data Science",
            "Web Development", "Framework",
            "Databases", "Backend", "Database",
            "Tools", "Platforms", "Cloud",
            "Soft Skills", "Soft",
        ]
        def sort_key(c):
            for i, o in enumerate(order):
                if o.lower() in c.lower():
                    return i
            return 99

        for cat in sorted(skill_groups.keys(), key=sort_key):
            line = f"<b>{cat}:</b>  {', '.join(skill_groups[cat])}"
            story.append(Paragraph(line, s_skill_line))

    # ── Experience ────────────────────────────────────────────────────────────
    if experience:
        story.extend(section_header("EXPERIENCE"))

        for exp in experience:
            job_title = exp.get("title", "")
            company   = exp.get("company", "")
            start     = exp.get("start_date", "")
            end       = "Present" if exp.get("is_current") else exp.get("end_date", "")
            desc      = exp.get("description", "")

            if start and end:
                date_str = f"{start} \u2013 {end}"
            elif start:
                date_str = start
            else:
                date_str = end or ""

            blk = []
            left_text = f"<b>{job_title}</b>" + (f" \u2014 <i>{company}</i>" if company else "")
            blk.append(two_col(
                Paragraph(left_text, s_bold_body),
                Paragraph(date_str, s_date),
            ))
            if desc:
                for line in desc.split("\n"):
                    line = line.strip().lstrip("\u2022\u25e6-\u2013").strip()
                    if line:
                        blk.append(Paragraph(f"\u25e6  {line}", s_bullet))
            blk.append(Spacer(1, 5))
            story.append(KeepTogether(blk))

    # ─── Build ────────────────────────────────────────────────────────────────
    doc.build(story)
    buf.seek(0)
    return buf.read()
