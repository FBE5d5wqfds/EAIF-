import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, CondPageBreak,
                                Image, KeepTogether, PageBreak)
from reportlab.lib.utils import ImageReader

import os
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "")
pdfmetrics.registerFont(TTFont("Carlito", HERE + "Carlito-Regular_fixed.ttf"))
pdfmetrics.registerFont(TTFont("Carlito-Bold", HERE + "Carlito-Bold_fixed.ttf"))
pdfmetrics.registerFont(TTFont("Carlito-Italic", HERE + "Carlito-Italic_fixed.ttf"))
addMapping("Carlito", 0, 0, "Carlito"); addMapping("Carlito", 1, 0, "Carlito-Bold"); addMapping("Carlito", 0, 1, "Carlito-Italic"); addMapping("Carlito", 1, 1, "Carlito-Bold")

# BFH layout as used in the group's own research brief
INK = colors.HexColor("#1f2a33"); MUTED = colors.HexColor("#6b7780"); SLATE = colors.HexColor("#697d91"); SLATE_DARK = colors.HexColor("#4a5a6a")
ZEBRA = colors.HexColor("#eef2f4"); LINE = colors.HexColor("#c9d1d6"); YELLOW = colors.HexColor("#fac300")
PAGE_W, PAGE_H = A4; MX = 57.0
CONTENT_W = PAGE_W - 2 * MX
TOP_RULE_Y = PAGE_H - 91.0; BOTTOM_RULE_Y = 40.0

def st(name, **kw):
    d = dict(fontName="Carlito", fontSize=10, leading=13.6, textColor=INK, alignment=TA_LEFT); d.update(kw); return ParagraphStyle(name, **d)
S = {"title": st("title", fontName="Carlito-Bold", fontSize=24, leading=28, spaceAfter=4),
     "subtitle": st("subtitle", fontSize=13, leading=17, textColor=SLATE, spaceAfter=12),
     "h1": st("h1", fontName="Carlito-Bold", fontSize=14.5, leading=18, textColor=SLATE_DARK, spaceBefore=12, spaceAfter=4),
     "h2": st("h2", fontName="Carlito-Bold", fontSize=11, leading=14, spaceBefore=7, spaceAfter=2),
     "body": st("body", spaceAfter=5),
     "bullet": st("bullet", leftIndent=12, bulletIndent=2, spaceAfter=2.5, bulletFontName="Helvetica", bulletFontSize=9),
     "small": st("small", fontSize=8.6, leading=11.4, textColor=MUTED, spaceAfter=3),
     "callout": st("callout", fontSize=10, leading=13.6),
     "cap": st("cap", fontName="Carlito-Italic", fontSize=8.6, leading=11, textColor=MUTED, spaceAfter=6)}

def inl(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = t.replace("\\*", "\x00")                     # \* in the source is a literal star, never markup
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(.+?)\*(?![\w*])", r"<i>\1</i>", t)
    return t.replace("\x00", "*")

def table(rows, fr, font=9, header=True):
    cell = st("tc", fontSize=font, leading=font + 2.6); cellh = st("tch", fontName="Carlito-Bold", fontSize=font, leading=font + 2.6, textColor=colors.white)
    data = [[Paragraph(inl(c), cellh if (header and i == 0) else cell) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[CONTENT_W * f for f in fr], repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), SLATE), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA])]
    t.setStyle(TableStyle(style)); return t

def callout(text):
    t = Table([[Paragraph(inl(text), S["callout"])]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ZEBRA), ("LINEBEFORE", (0, 0), (0, -1), 3, SLATE), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t

def blocks_to_story(blocks):
    st_ = []
    for b in blocks:
        k = b[0]
        if k == "h1": st_ += [CondPageBreak(45), Paragraph(inl(b[1]), S["h1"])]
        elif k == "h2": st_.append(Paragraph(inl(b[1]), S["h2"]))
        elif k == "p": st_.append(Paragraph(inl(b[1]), S["body"]))
        elif k in ("note", "small"): st_.append(Paragraph(inl(b[1]), S["small"]))
        elif k == "bul":
            for t in b[1]: st_.append(Paragraph(inl(t), S["bullet"], bulletText="•"))
            st_.append(Spacer(1, 3))
        elif k == "tbl": st_ += [table(b[1], b[2], (b[3] if len(b) > 3 else 9) + 0.2), Spacer(1, 7)]
        elif k == "callout": st_ += [callout(b[1]), Spacer(1, 7)]
        elif k == "draw": st_ += [b[1], Spacer(1, 4)]
        elif k == "img":
            path, frac = b[1], b[2]; iw, ih = ImageReader(path).getSize(); w = CONTENT_W * frac
            parts = [Image(path, width=w, height=w * ih / iw)]
            if len(b) > 3: parts.append(Paragraph(inl(b[3]), S["cap"]))
            st_.append(KeepTogether(parts))
        elif k == "pb": st_.append(PageBreak())
    return st_

def build_pdf(path, blocks, title, subtitle, header_text, footer_text, meta=None, purpose=None):
    """BFH layout: yellow rule under the header, logo top right, title block with an Item/Details table and a 'Purpose.' callout."""
    def on_page(c, doc):
        c.saveState()
        iw, ih = ImageReader(HERE + "bfh_logo.png").getSize(); w = 87.4; h = w * ih / iw
        c.drawImage(HERE + "bfh_logo.png", PAGE_W - MX - w, PAGE_H - 25.5 - h, width=w, height=h, mask="auto")
        c.setFont("Carlito", 9.5); c.setFillColor(MUTED); c.drawString(MX, TOP_RULE_Y + 5, header_text)
        c.setStrokeColor(YELLOW); c.setLineWidth(1.2); c.line(MX, TOP_RULE_Y, PAGE_W - MX, TOP_RULE_Y)
        c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(MX, BOTTOM_RULE_Y, PAGE_W - MX, BOTTOM_RULE_Y)
        c.setFont("Carlito", 8.5); c.setFillColor(MUTED); c.drawString(MX, BOTTOM_RULE_Y - 11, footer_text); c.drawRightString(PAGE_W - MX, BOTTOM_RULE_Y - 11, "Page %d" % doc.page)
        c.restoreState()
    doc = BaseDocTemplate(path, pagesize=A4, leftMargin=MX, rightMargin=MX, topMargin=108, bottomMargin=52,
                          title=re.sub(r"\*", "", title), author="Group_8")
    fr = Frame(MX, 52, CONTENT_W, PAGE_H - 108 - 52, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[fr], onPage=on_page)])
    story = [Paragraph(inl(title), S["title"]), Paragraph(inl(subtitle), S["subtitle"])]
    if meta:
        story += [table([["Item", "Details"]] + meta, [0.22, 0.78], 9.2), Spacer(1, 9)]
    if purpose:
        story += [callout("**Purpose.** " + purpose), Spacer(1, 6)]
    doc.build(story + blocks_to_story(blocks)); return path
