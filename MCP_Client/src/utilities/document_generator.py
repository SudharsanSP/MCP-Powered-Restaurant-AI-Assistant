"""
document_generator.py
---------------------
Builds formatted Word (.docx) documents from structured section data.

Supported document types:
  - sales_report
  - menu_review
  - menu_proposal
  - meeting_minutes
  - sop
  - performance_report

Each section dict may contain:
  heading  (str)         — section title
  content  (str)         — paragraph text
  table    (list[dict])  — list of row dicts; keys become column headers
  bullets  (list[str])   — bulleted list items
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from utilities.logger import get_logger

logger = get_logger(__name__)

# Folder where generated documents are stored, relative to this file's project
_DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "documents"
_DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

# ── brand colours ──────────────────────────────────────────────────────────────
_BROWN = RGBColor(0x6B, 0x3A, 0x2A)   # coffee brown  — headings / title
_TAN   = RGBColor(0xF5, 0xF0, 0xEB)   # warm cream    — table header bg
_DARK  = RGBColor(0x1F, 0x1F, 0x1F)   # near-black    — body text


def _set_cell_bg(cell, hex_color: str) -> None:
    """Fill a table cell background with a hex colour string (e.g. 'F5F0EB')."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _add_horizontal_rule(doc: Document) -> None:
    """Insert a thin horizontal line paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "6B3A2A")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _style_table(table) -> None:
    """Apply alternating row shading and header formatting to a table."""
    for row_idx, row in enumerate(table.rows):
        for cell in row.cells:
            if row_idx == 0:
                _set_cell_bg(cell, "6B3A2A")
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        run.font.size = Pt(10)
            elif row_idx % 2 == 0:
                _set_cell_bg(cell, "F5F0EB")


def _add_section(doc: Document, section: dict) -> None:
    """Render one section dict into the document."""
    heading = section.get("heading", "")
    content = section.get("content", "")
    table_data: list[dict] = section.get("table", [])
    bullets: list[str] = section.get("bullets", [])

    if heading:
        h = doc.add_heading(heading, level=2)
        h.runs[0].font.color.rgb = _BROWN
        h.runs[0].font.size = Pt(13)

    if content:
        para = doc.add_paragraph(content)
        para.runs[0].font.size = Pt(11)
        para.runs[0].font.color.rgb = _DARK
        para.paragraph_format.space_after = Pt(6)

    if bullets:
        for item in bullets:
            bp = doc.add_paragraph(style="List Bullet")
            run = bp.add_run(item)
            run.font.size = Pt(11)
            run.font.color.rgb = _DARK

    if table_data:
        columns = list(table_data[0].keys())
        tbl = doc.add_table(rows=1 + len(table_data), cols=len(columns))
        tbl.style = "Table Grid"
        # Header row
        hdr_cells = tbl.rows[0].cells
        for col_idx, col_name in enumerate(columns):
            hdr_cells[col_idx].text = col_name.replace("_", " ").title()
        # Data rows
        for row_idx, row_data in enumerate(table_data, start=1):
            row_cells = tbl.rows[row_idx].cells
            for col_idx, col_name in enumerate(columns):
                value = row_data.get(col_name, "")
                row_cells[col_idx].text = str(value)
        _style_table(tbl)
        doc.add_paragraph()  # breathing room after table


def generate_document(
    title: str,
    document_type: str,
    sections: list[dict],
    metadata: dict | None = None,
) -> str:
    """
    Build a branded .docx file and return its filename.

    Parameters
    ----------
    title         : Document title shown on the cover page.
    document_type : Slug used in the filename (e.g. 'sales_report').
    sections      : List of section dicts with keys:
                      heading, content, table, bullets
    metadata      : Extra key/value pairs rendered in the footer line.

    Returns
    -------
    filename (str) — the .docx filename (not full path).
    """
    logger.info("Generating Word document: %s", title)
    doc = Document()

    # ── page margins ────────────────────────────────────────────────────────
    for section in doc.sections:
        section.top_margin    = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin   = Inches(1.2)
        section.right_margin  = Inches(1.2)

    # ── cover / title block ─────────────────────────────────────────────────
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(title)
    title_run.bold = True
    title_run.font.size = Pt(20)
    title_run.font.color.rgb = _BROWN

    subtitle_para = doc.add_paragraph()
    subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle_para.add_run("Coffee Shop — Manager Report")
    sub_run.font.size = Pt(12)
    sub_run.font.color.rgb = RGBColor(0x88, 0x66, 0x55)

    # generated-on line
    meta = metadata or {}
    gen_date = meta.get("date", datetime.now().strftime("%B %d, %Y"))
    gen_by   = meta.get("generated_by", "Autonomous Manager Agent")
    meta_para = doc.add_paragraph()
    meta_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = meta_para.add_run(f"Generated on {gen_date}  |  {gen_by}")
    meta_run.font.size = Pt(10)
    meta_run.italic = True
    meta_run.font.color.rgb = RGBColor(0x77, 0x77, 0x77)

    _add_horizontal_rule(doc)
    doc.add_paragraph()

    # ── sections ────────────────────────────────────────────────────────────
    for sec in sections:
        _add_section(doc, sec)

    # ── footer line ─────────────────────────────────────────────────────────
    _add_horizontal_rule(doc)
    footer_para = doc.add_paragraph()
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer_para.add_run(
        "Confidential — Brew Buddy Coffee Shop  |  Auto-generated document"
    )
    footer_run.font.size = Pt(9)
    footer_run.italic = True
    footer_run.font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)

    # ── save ────────────────────────────────────────────────────────────────
    safe_slug = re.sub(r"[^a-z0-9_]", "_", document_type.lower())
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = f"{safe_slug}_{timestamp}.docx"
    file_path  = _DOCUMENTS_DIR / filename
    doc.save(str(file_path))
    logger.info("Document saved: %s", filename)
    return filename
