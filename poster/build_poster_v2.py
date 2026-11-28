"""PARCO poster in the style of the reference SRP poster.

    python poster/build_poster_v2.py                # A1 (594 x 841 mm)
    python poster/build_poster_v2.py --size A0

Design follows the reference: white sheet, centred title block with a
supervisor line and a rule, then rounded pastel cards with drop shadows, each
with a centred underlined heading and dark inset boxes for the points that
must land. Numbers come from report/data.py.
"""

from __future__ import annotations

import argparse
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "report"))
import data as D              # noqa: E402
import figures_v2 as FV       # noqa: E402

SIZES = {"A1": (594 * mm, 841 * mm), "A0": (841 * mm, 1189 * mm)}

# palette taken from the reference poster
INK = colors.HexColor("#2B2B2B")
NAVY = colors.HexColor("#1F4E79")
BLUE_FILL = colors.HexColor("#D8E8F6")
BLUE_EDGE = colors.HexColor("#B9D4EC")
GREY_FILL = colors.HexColor("#EAEAEA")
GREY_EDGE = colors.HexColor("#D2D2D2")
PEACH_FILL = colors.HexColor("#F9DAC2")
PEACH_EDGE = colors.HexColor("#EEC3A2")
DARK_BOX = colors.HexColor("#4A4A4A")
NAVY_BOX = colors.HexColor("#1F4E79")
SHADOW = colors.HexColor("#C9C9C9")
MUTED = colors.HexColor("#55616B")
TEAL = colors.HexColor("#0E8A72")
ORANGE = colors.HexColor("#D9531E")
GOOD = colors.HexColor("#17794A")
BAD = colors.HexColor("#B23A1F")


def register_fonts():
    import matplotlib
    base = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    for n, f in (("DJ", "DejaVuSans.ttf"), ("DJ-B", "DejaVuSans-Bold.ttf"),
                 ("DJ-I", "DejaVuSans-Oblique.ttf"),
                 ("DJ-BI", "DejaVuSans-BoldOblique.ttf"),
                 ("DJM", "DejaVuSansMono.ttf")):
        p = os.path.join(base, f)
        if os.path.exists(p):
            pdfmetrics.registerFont(TTFont(n, p))
    pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B",
                                  italic="DJ-I", boldItalic="DJ-BI")


register_fonts()
F, FB, FI, FM = "DJ", "DJ-B", "DJ-I", "DJM"
_S: list = []


def st(**kw):
    base = dict(name=f"s{len(_S)}", fontName=F, fontSize=20, leading=27,
                textColor=INK, alignment=TA_LEFT)
    base.update(kw)
    s = ParagraphStyle(**base)
    _S.append(s)
    return s


S_TITLE = st(fontName=FB, fontSize=52, leading=60, alignment=TA_CENTER)
S_AUTH = st(fontSize=28, leading=38, alignment=TA_CENTER)
S_SUP = st(fontName=FI, fontSize=27, leading=36, alignment=TA_CENTER, textColor=NAVY)
S_CARD = st(fontName=FB, fontSize=33, leading=40, alignment=TA_CENTER, textColor=NAVY)
S_CARDK = st(fontName=FB, fontSize=33, leading=40, alignment=TA_CENTER, textColor=INK)
S_BODY = st()
S_BODYC = st(alignment=TA_CENTER)
S_WHITE = st(textColor=colors.white)
S_WHITEC = st(textColor=colors.white, alignment=TA_CENTER)
S_SMALL = st(fontSize=17, leading=23, textColor=MUTED)
S_CAP = st(fontSize=18, leading=24, textColor=NAVY, alignment=TA_CENTER)
S_CODE = st(fontName=FM, fontSize=17, leading=24)
S_TH = st(fontName=FB, fontSize=17, leading=23, textColor=colors.white)
S_TD = st(fontSize=18, leading=24)
S_TDC = st(fontSize=18, leading=24, alignment=TA_CENTER)


def Pg(t, s=S_BODY):
    return Paragraph(t, s)


def Ticks(items, s=S_BODY):
    """The reference uses ✓ bullets inside its blue card."""
    return [Paragraph(f"✓&nbsp;&nbsp;{t}", s) for t in items]


def Dots(items, s=S_BODY):
    return [Paragraph(f"•&nbsp;&nbsp;{t}", s) for t in items]


def Img(path, width):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    return Image(path, width=width, height=width * h / w)


def Tbl(header, rows, widths, highlight=()):
    data = [[Paragraph(h, S_TH) for h in header]]
    for r in rows:
        data.append([Paragraph(str(c), S_TD if i == 0 else S_TDC)
                     for i, c in enumerate(r)])
    t = Table(data, colWidths=widths)
    style = [("BACKGROUND", (0, 0), (-1, 0), NAVY),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("BACKGROUND", (0, 1), (-1, -1), colors.white),
             ("GRID", (0, 0), (-1, -1), .8, colors.HexColor("#CFD8DF")),
             ("TOPPADDING", (0, 0), (-1, -1), 6),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
    for r in highlight:
        style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#E3F1EC")))
    t.setStyle(TableStyle(style))
    return t


class Box:
    """A dark rounded inset, as the reference uses for its key statements."""

    def __init__(self, items, fill=DARK_BOX, pad=14):
        self.items, self.fill, self.pad = items, fill, pad

    def wrapOn(self, c, w, h):
        self.w = w
        total = self.pad * 2
        self._sized = []
        for it in self.items:
            _, ih = it.wrapOn(c, w - 2 * self.pad, 10000)
            self._sized.append((it, ih))
            total += ih + 6
        self.h = total - 6
        return w, self.h

    def drawOn(self, c, x, y):
        c.setFillColor(self.fill)
        c.setStrokeColor(self.fill)
        c.roundRect(x, y, self.w, self.h, 9, stroke=1, fill=1)
        yy = y + self.h - self.pad
        for it, ih in self._sized:
            it.drawOn(c, x + self.pad, yy - ih)
            yy -= ih + 6


class Col:
    def __init__(self, c, x, top, w, bottom):
        self.c, self.x, self.y, self.w, self.bottom = c, x, top, w, bottom

    def room(self):
        return self.y - self.bottom

    def card(self, title, items, fill=BLUE_FILL, edge=BLUE_EDGE,
             tstyle=S_CARD, pad=20, gap=22, rule=True):
        inner = self.w - 2 * pad
        head = Pg(title, tstyle)
        _, hh = head.wrapOn(self.c, inner, 10000)

        sized = []
        total = pad * 2 + hh + (16 if rule else 10)
        for it in items:
            _, ih = it.wrapOn(self.c, inner, 10000)
            sized.append((it, ih))
            total += ih + 11
        total -= 11

        top = self.y
        # drop shadow, as in the reference
        self.c.setFillColor(SHADOW)
        self.c.setStrokeColor(SHADOW)
        self.c.roundRect(self.x + 3.2 * mm, top - total - 3.2 * mm,
                         self.w, total, 10 * mm, stroke=1, fill=1)
        self.c.setFillColor(fill)
        self.c.setStrokeColor(edge)
        self.c.setLineWidth(1.4)
        self.c.roundRect(self.x, top - total, self.w, total, 10 * mm,
                         stroke=1, fill=1)

        y = top - pad
        head.drawOn(self.c, self.x + pad, y - hh)
        y -= hh + 4
        if rule:
            self.c.setStrokeColor(NAVY)
            self.c.setLineWidth(1.6)
            cx = self.x + self.w / 2
            half = inner * .40
            self.c.line(cx - half, y, cx + half, y)
            y -= 12
        else:
            y -= 6
        for it, ih in sized:
            it.drawOn(self.c, self.x + pad, y - ih)
            y -= ih + 11
        self.y = top - total - gap
        return total


def build(out_path, size="A1"):
    PW, PH = SIZES[size]
    W, H = SIZES["A1"]                 # lay out at A1; A0 is a uniform scale
    figs = FV.build(os.path.join(HERE, "_figs_v2"))
    A = os.path.join(HERE, "assets")

    c = pdfcanvas.Canvas(out_path, pagesize=(PW, PH))
    c.setTitle("Extending PARCO — SRP Group 9")
    c.setAuthor("SRP Group 9, Universität Hildesheim")
    if size != "A1":
        c.scale(PW / W, PH / H)

    M = 26 * mm
    inner_w = W - 2 * M

    # ----------------------------------------------------------- title block
    y = H - 22 * mm
    for p, gap in ((Pg("EXTENDING PARCO", S_TITLE), 6 * mm),
                   (Pg("Akshai Athota &nbsp;•&nbsp; Charitha Yetukuri &nbsp;•&nbsp; "
                       "Nitin Sharma &nbsp;•&nbsp; Shehroz Khan &nbsp;•&nbsp; "
                       "Mina George Soliman Hanna", S_AUTH), 9 * mm),
                   (Pg("Does parallel decoding cost solution quality?  "
                       "Controlled experiments on min-max HCVRP", S_SUP), 7 * mm)):
        _, h = p.wrapOn(c, inner_w, 10000)
        p.drawOn(c, M, y - h)
        y -= h + gap

    c.setStrokeColor(NAVY)
    c.setLineWidth(2.4)
    c.line(M + 10 * mm, y, W - M - 10 * mm, y)
    c.setStrokeColor(colors.HexColor("#9FC0DC"))
    c.setLineWidth(1.2)
    c.line(M + 10 * mm, y - 2.6 * mm, W - M - 10 * mm, y - 2.6 * mm)
    y -= 12 * mm

    # -------------------------------------------------------------- columns
    GUT = 14 * mm
    lw = inner_w * .435
    rw = inner_w - lw - GUT
    left = Col(c, M, y, lw, 20 * mm)
    right = Col(c, M + lw + GUT, y, rw, 20 * mm)
    li, ri = lw - 40, rw - 40

    # ============================ LEFT ====================================
    left.card("The Challenge", [
        Pg("<b>M</b> vehicles serve <b>N</b> customers from one depot. Vehicles "
           "differ in <b>capacity</b> and <b>speed</b>, and we minimise when the "
           "<i>last</i> van finishes — so the problem is about <b>balance</b>, not "
           "total distance.", S_BODYC),
        Box([Pg("PARCO makes this fast by letting every vehicle choose at the same "
                "decoder step, then repairing collisions with a fixed priority "
                "rule. What does that speed cost in solution quality?", S_WHITEC)],
            fill=NAVY_BOX),
        Pg("<b>Our approach</b>", S_BODY),
        Pg("Remove the collisions instead of repairing them, and make the number of "
           "agents that commit per pass a single tunable parameter <b>k</b>.",
           S_BODYC),
        *Ticks(["Collision-free by construction — the conflict handler never runs",
                "k = 1 is fully sequential, k = M is one-shot joint assignment",
                "Every change measured against a PARCO we trained ourselves"]),
    ], fill=BLUE_FILL, edge=BLUE_EDGE)

    left.card("What PARCO Does", [
        Img(os.path.join(A, "parco_concept.jpg"), li * .72),
        Pg("Sequential (top) versus parallel (bottom) construction", S_SMALL),
        Box([Pg("<b>Three mechanisms:</b> communication layers let agents exchange "
                "context while decoding; a multiple pointer mechanism gives every "
                "agent its own next-node distribution; a priority conflict handler "
                "settles ties. Only the third is a hand-written rule — and it is "
                "the one we replace.", S_WHITE)], fill=DARK_BOX),
        Pg("The action space is <b>M + N</b>, not N: the depot is replicated once "
           "per agent — otherwise the first van home would mark it visited for "
           "everyone, and no agent could express “stay”.", S_SMALL),
    ], fill=GREY_FILL, edge=GREY_EDGE, tstyle=S_CARDK)

    left.card("Top Results", [
        Img(figs["pareto"], li * .85),
        Pg("Each model trained <i>and</i> evaluated at its own k. Parallel PARCO "
           "sits inside the shaded region: slower <b>and</b> worse than k = 2.",
           S_BODYC),
        Pg("12 HCVRP test sets · 1 280 instances each · greedy decoding", S_CAP),
    ], fill=BLUE_FILL, edge=BLUE_EDGE)

    # ============================ RIGHT ===================================
    rows = []
    for label, d in (("Parallel PARCO", D.CONTROL), ("k = 1  sequential", D.K_TRAINED[1]),
                     ("k = 2", D.K_TRAINED[2]), ("k = 4", D.K_TRAINED[4]),
                     ("k = 7  joint", D.K_TRAINED[7])):
        if d is D.CONTROL:
            gap_cell, win = "—", "—"
        else:
            g = D.gap(d)
            col = GOOD if g < 0 else BAD
            gap_cell = f'<font color="#{col.hexval()[2:]}"><b>{g:+.2f}%</b></font>'
            win = f"{D.wins(d)}/12"
        rows.append([label, f"{D.mean_cost(d):.4f}", gap_cell, win,
                     f"{D.mean_steps(d):.1f}"])

    right.card("Our Method: one knob, k", [
        Pg("<b>k</b> = how many (agent, node) pairs are committed per decoder pass. "
           "Our supervisor observed that in the fully sequential limit two of our "
           "ideas are <i>the same thing</i> — so they became one parameter.",
           S_BODYC),
        Img(figs["spectrum"], ri),
        Img(figs["decoding"], ri * .95),
        Box([Pg("The k picks reuse the <b>same</b> logits tensor, so one pass costs "
                "the same whatever k is. That is what makes decoder passes a fair "
                "unit of compute — and what lets us ask whether the sequential win "
                "is simply bought with extra inference.", S_WHITE)], fill=DARK_BOX),
        Pg("We also corrected the inherited logit clip. Written as "
           "<b>φ(z) = g·tanh(z/τ)</b>, PARCO's C·tanh(z) has slope 10 at the origin "
           "— it <i>amplifies</i> rather than clips, an effective 10× temperature "
           "drop. The textbook form is <b>−0.93%</b> better on 12/12 sets.",
           S_BODYC),
    ], fill=PEACH_FILL, edge=PEACH_EDGE, tstyle=S_CARDK)

    right.card("Key Findings", [
        Tbl(["Method", "Cost", "Gap", "Wins", "Passes"], rows,
            [ri * .30, ri * .17, ri * .20, ri * .15, ri * .18], highlight=(2, 3)),
        Box([*Dots([
            "<b>k = 2 dominates parallel PARCO</b> — better on all 12 test sets, "
            "34% fewer decoder passes, 16% less training time per epoch. Not a "
            "trade-off: better on every axis at once.",
            "<b>The advantage scales with fleet size</b>, from −3.0% at M = 3 to "
            "−6.2% at M = 7.",
            "<b>The win is not bought with compute.</b> Given up to 32× the "
            "inference budget, parallel PARCO never reaches a single greedy k = 1 "
            "rollout.",
        ], S_WHITE)], fill=DARK_BOX),
        Pg("<b>Honest caveat:</b> surplus budget was spent only as i.i.d. sampling "
           "at temperature 1, which is weak for <i>all</i> models here — best-of-32 "
           "only just returns to the greedy cost. One seed per configuration, so "
           "the small tanh effect still needs error bars.", S_SMALL),
        Img(figs["scaling"], ri * .52),
        Pg("The advantage grows with fleet size — the mechanism confirming itself.",
           S_BODYC),
        Pg("<b>Next:</b> a decoding-only k sweep to separate training-at-k from "
           "decoding-at-k; a learned, parametric conflict handler; and extending k "
           "to OMDCPDP and FFSP.", S_SMALL),
    ], fill=GREY_FILL, edge=GREY_EDGE, tstyle=S_CARDK)

    # --------------------------------------------------------------- footer
    c.setFillColor(MUTED)
    c.setFont(F, 17)
    c.drawCentredString(W / 2, 12 * mm,
                        "Base work: Berto et al., PARCO, NeurIPS 2025   ·   "
                        "Code, report and an interactive delivery simulator:  "
                        "github.com/Akshai-Athota/parco")

    c.showPage()
    c.save()
    return out_path, (left.room() / mm, right.room() / mm)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", choices=list(SIZES), default="A1")
    ap.add_argument("--out", default=None)
    o = ap.parse_args()
    out = o.out or os.path.join(HERE, f"PARCO_SRP_Poster_v2_{o.size}.pdf")
    path, room = build(out, o.size)
    print(f"wrote {path}  ({os.path.getsize(path)//1024} KB)")
    print(f"remaining room — left {room[0]:.0f} mm, right {room[1]:.0f} mm")
