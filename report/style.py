"""Palette, fonts, paragraph styles and flowable helpers for the report."""

from __future__ import annotations

import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# --------------------------------------------------------------- palette --
NAVY = colors.HexColor("#12304A")
NAVY2 = colors.HexColor("#1F3B57")
INK = colors.HexColor("#25384A")
MUTED = colors.HexColor("#5B7085")
RULE = colors.HexColor("#D4DEE6")
SOFT = colors.HexColor("#EFF4F7")
ORANGE = colors.HexColor("#E2561F")
TEAL = colors.HexColor("#12927A")
GOLD = colors.HexColor("#D9A21B")
PURPLE = colors.HexColor("#7E5AA8")
GOOD = colors.HexColor("#1C7A4A")
BAD = colors.HexColor("#B23A1F")
WARMBG = colors.HexColor("#FDF3E6")
WARMLN = colors.HexColor("#F2DFC2")
MINTBG = colors.HexColor("#E8F3F0")
MINTLN = colors.HexColor("#CFE4DE")
REDBG = colors.HexColor("#FDECE4")
REDLN = colors.HexColor("#F6D6C6")


def register_fonts():
    """DejaVu ships with matplotlib and covers the arrows and maths glyphs."""
    import matplotlib
    base = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    faces = {"DejaVu": "DejaVuSans.ttf", "DejaVu-Bold": "DejaVuSans-Bold.ttf",
             "DejaVu-Oblique": "DejaVuSans-Oblique.ttf",
             "DejaVu-BoldOblique": "DejaVuSans-BoldOblique.ttf",
             "DejaVuMono": "DejaVuSansMono.ttf",
             "DejaVuMono-Bold": "DejaVuSansMono-Bold.ttf"}
    for name, fn in faces.items():
        path = os.path.join(base, fn)
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
    pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold",
                                  italic="DejaVu-Oblique",
                                  boldItalic="DejaVu-BoldOblique")
    pdfmetrics.registerFontFamily("DejaVuMono", normal="DejaVuMono",
                                  bold="DejaVuMono-Bold")


register_fonts()
SS = getSampleStyleSheet()
F, FB, FI, FM = "DejaVu", "DejaVu-Bold", "DejaVu-Oblique", "DejaVuMono"


def _s(name, **kw):
    base = dict(name=name, fontName=F, fontSize=9.4, leading=14.2, textColor=INK,
                spaceAfter=6)
    base.update(kw)
    return ParagraphStyle(**base)


ST = {
    "title":   _s("title", fontName=FB, fontSize=27, leading=32, textColor=NAVY, spaceAfter=10),
    "subtitle": _s("subtitle", fontSize=12.5, leading=18, textColor=MUTED, spaceAfter=18),
    "h1":      _s("h1", fontName=FB, fontSize=17, leading=22, textColor=NAVY,
                  spaceBefore=16, spaceAfter=9),
    "h2":      _s("h2", fontName=FB, fontSize=12.4, leading=17, textColor=NAVY2,
                  spaceBefore=13, spaceAfter=6),
    "h3":      _s("h3", fontName=FB, fontSize=10.2, leading=14, textColor=NAVY2,
                  spaceBefore=9, spaceAfter=4),
    "body":    _s("body"),
    "small":   _s("small", fontSize=8.4, leading=12.2, textColor=MUTED),
    "cap":     _s("cap", fontSize=8.2, leading=11.6, textColor=MUTED,
                  alignment=TA_CENTER, spaceBefore=4, spaceAfter=12),
    "code":    _s("code", fontName=FM, fontSize=8.0, leading=11.4, textColor=INK,
                  spaceBefore=2, spaceAfter=2),
    "bullet":  _s("bullet", leftIndent=12, bulletIndent=2, spaceAfter=4),
    "th":      _s("th", fontName=FB, fontSize=8.1, leading=10.6, textColor=colors.white),
    "td":      _s("td", fontSize=8.3, leading=11.2),
    "tdc":     _s("tdc", fontSize=8.3, leading=11.2, alignment=TA_CENTER),
    "toc":     _s("toc", fontSize=9.6, leading=16),
}


# ------------------------------------------------------------- flowables --
def P(txt, style="body"):
    return Paragraph(txt, ST[style])


def UL(items, style="bullet"):
    return [Paragraph(f"• {t}", ST[style]) for t in items]


def OL(items, style="bullet"):
    return [Paragraph(f"<b>{i+1}.</b>  {t}", ST[style]) for i, t in enumerate(items)]


def CODE(lines, width=16.4 * cm):
    body = [[Paragraph(ln.replace(" ", "&nbsp;") or "&nbsp;", ST["code"])] for ln in lines]
    t = Table(body, colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F7F9")),
        ("BOX", (0, 0), (-1, -1), .6, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    return [Spacer(1, 5), t, Spacer(1, 8)]


def CALLOUT(title, body, kind="note", width=16.4 * cm):
    bg, ln, fg = {"note": (SOFT, RULE, NAVY2), "warn": (WARMBG, WARMLN, colors.HexColor("#8A5B06")),
                  "good": (MINTBG, MINTLN, TEAL), "bad": (REDBG, REDLN, BAD)}[kind]
    inner = []
    if title:
        inner.append(Paragraph(f'<font color="#{fg.hexval()[2:]}"><b>{title}</b></font>', ST["body"]))
    inner.append(Paragraph(body, ST["body"]))
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), .7, ln),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [Spacer(1, 4), t, Spacer(1, 9)]


def TABLE(header, rows, widths, align_right_from=1, highlight=(), plain=False):
    data = [] if plain else [[Paragraph(h, ST["th"]) for h in header]]
    for r in rows:
        line = []
        for i, cell in enumerate(r):
            txt = cell if isinstance(cell, str) else str(cell)
            line.append(Paragraph(txt, ST["td"] if i == 0 else ST["tdc"]))
        data.append(line)
    t = Table(data, colWidths=widths, repeatRows=0 if plain else 1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.white if plain else NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), .5, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    if plain:
        style.append(("ALIGN", (0, 0), (-1, -1), "LEFT"))
    for r in highlight:
        style.append(("BACKGROUND", (0, r), (-1, r), MINTBG))
    t.setStyle(TableStyle(style))
    return [Spacer(1, 3), t, Spacer(1, 10)]


def FIG(path, caption, width=15.4 * cm):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    img = Image(path, width=width, height=width * h / w)
    return [Spacer(1, 5), img, P(caption, "cap")]


def pct(v, nd=2):
    col = GOOD if v < 0 else BAD
    return f'<font color="#{col.hexval()[2:]}"><b>{v:+.{nd}f}%</b></font>'


