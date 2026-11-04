from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
INK = colors.HexColor("#1f2933"); MUTED = colors.HexColor("#5b6670"); ACCENT = colors.HexColor("#1d4e89")
ACCENT_LIGHT = colors.HexColor("#e8eff7"); RULE = colors.HexColor("#c9d1d9")
BASE, BOLD, ITAL = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
def style(name, **kw):
    d = dict(fontName=BASE, fontSize=9.5, leading=13, textColor=INK, alignment=TA_LEFT); d.update(kw)
    return ParagraphStyle(name, **d)
S = {
 "title": style("title", fontName=BOLD, fontSize=19, leading=23, textColor=ACCENT, spaceAfter=2),
 "subtitle": style("subtitle", fontSize=10.5, leading=14, textColor=MUTED, spaceAfter=6),
 "h1": style("h1", fontName=BOLD, fontSize=12.5, leading=16, textColor=ACCENT, spaceBefore=10, spaceAfter=4),
 "body": style("body", spaceAfter=5),
 "bullet": style("bullet", leftIndent=12, bulletIndent=2, spaceAfter=2.5),
 "note": style("note", fontSize=8.8, leading=12, textColor=MUTED, spaceAfter=4),
 "cell": style("cell", fontSize=8.6, leading=11.4),
 "cellb": style("cellb", fontName=BOLD, fontSize=8.6, leading=11.4),
}
