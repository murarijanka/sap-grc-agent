"""Build the PDF report: page 1 summary, findings by area, appendix."""
from collections import Counter
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

from .checks import CHECKS

SEV_COLOUR = {"High": colors.HexColor("#b42318"), "Medium": colors.HexColor("#b54708"), "Low": colors.HexColor("#475467")}
AREAS = ["Rule set", "Controls", "Emergency"]
CREDIT = "SAP GRC Readiness Agent - designed and directed by Murari Janka, built with Claude (Anthropic). Apache 2.0."
DISCLAIMER = ("Read-only analysis of uploaded exports. Findings come from fixed rules; people decide every fix. "
              "Not affiliated with SAP SE.")


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Cell", parent=s["BodyText"], fontSize=8, leading=10))
    s.add(ParagraphStyle("Small", parent=s["BodyText"], fontSize=8, textColor=colors.HexColor("#475467")))
    return s


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(15 * mm, 10 * mm, CREDIT)
    canvas.drawRightString(195 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _grid(data, widths, header_bg="#f2f4f7"):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d0d5dd")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def build_pdf(path, findings, skipped, inputs, run_date=None, org_name="Sample company", claude_summary=None, explanations=None):
    run_date = run_date or datetime.now()
    st = _styles()
    P = lambda t, style="Cell": Paragraph(t, st[style])  # noqa: E731
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=18 * mm,
                            title="SAP GRC readiness report", author="SAP GRC Readiness Agent")
    story = []

    # Page 1: summary
    sev = Counter(f.severity for f in findings)
    story += [P("SAP GRC readiness report", "Title"),
              P(f"{org_name} &middot; run on {run_date:%d %b %Y}", "Small"), Spacer(1, 6 * mm)]
    summary = [["High", "Medium", "Low", "Checks run", "Checks skipped"],
               [sev["High"], sev["Medium"], sev["Low"], len(CHECKS) - len(skipped), len(skipped)]]
    t = _grid(summary, [34 * mm] * 5)
    t.setStyle(TableStyle([("FONTSIZE", (0, 1), (-1, 1), 16), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                           ("TEXTCOLOR", (0, 1), (0, 1), SEV_COLOUR["High"]),
                           ("TEXTCOLOR", (1, 1), (1, 1), SEV_COLOUR["Medium"]),
                           ("TOPPADDING", (0, 1), (-1, 1), 6), ("BOTTOMPADDING", (0, 1), (-1, 1), 6)]))
    story += [t, Spacer(1, 6 * mm)]
    by_area = Counter(f.area for f in findings)
    story += [P("Findings by area", "Heading3"),
              _grid([["Area", "Findings"]] + [[a, by_area[a]] for a in AREAS], [60 * mm, 30 * mm]),
              Spacer(1, 6 * mm)]
    if claude_summary:
        story += [P("Summary (written by Claude from the findings)", "Heading3"), P(claude_summary, "BodyText"), Spacer(1, 4 * mm)]
    story += [P("Top 10 findings", "Heading3")]
    top = [["#", "Severity", "Area", "Record", "Reason"]]
    for i, f in enumerate(findings[:10], 1):
        top.append([i, P(f"<font color='{SEV_COLOUR[f.severity].hexval()}'><b>{f.severity}</b></font>"),
                    f.area, P(f.record), P(f.reason)])
    story += [_grid(top, [8 * mm, 18 * mm, 20 * mm, 45 * mm, 89 * mm]), Spacer(1, 6 * mm),
              P(DISCLAIMER, "Small"), PageBreak()]

    # Findings by area
    for area in AREAS:
        items = [f for f in findings if f.area == area]
        story.append(P(f"{area} ({len(items)})", "Heading2"))
        if not items:
            story += [P("No findings.", "BodyText"), Spacer(1, 4 * mm)]
            continue
        rows = [["Check", "Severity", "Record", "Reason", "Recommended action", "Source"]]
        for f in items:
            why = (explanations or {}).get(findings.index(f))
            reason = f.reason + (f"<br/><i>{why}</i>" if why else "")
            rows.append([f.check_id,
                         P(f"<font color='{SEV_COLOUR[f.severity].hexval()}'><b>{f.severity}</b></font>"),
                         P(f.record), P(reason), P(f.action), P("<br/>".join(f.source))])
        story += [_grid(rows, [11 * mm, 16 * mm, 32 * mm, 50 * mm, 40 * mm, 31 * mm]), Spacer(1, 6 * mm)]

    # Appendix
    story += [PageBreak(), P("Appendix", "Heading2"), P("Checks", "Heading3")]
    rows = [["#", "Check", "Status"]]
    for i, fn in enumerate(CHECKS, 1):
        rows.append([i, P(fn.__doc__.strip().splitlines()[0] if fn.__doc__ else fn.__name__),
                     "Skipped (input not supplied)" if i in skipped else "Run"])
    story += [_grid(rows, [8 * mm, 120 * mm, 52 * mm]), Spacer(1, 4 * mm), P("Input files", "Heading3")]
    rows = [["Upload", "File", "Rows"]] + [[k, v[0], v[1]] for k, v in inputs.items()]
    story += [_grid(rows, [40 * mm, 100 * mm, 40 * mm])]
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path
