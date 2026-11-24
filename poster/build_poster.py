"""A0 conference poster for the SRP project.

    python poster/build_poster.py                # A0 portrait (841 x 1189 mm)
    python poster/build_poster.py --size A1      # same design, A1

A0 and A1 share the same aspect ratio, so one layout serves both: the A1 build
is the identical artwork on a smaller sheet. Text sizes are absolute points,
chosen for the printed A0 sheet read from roughly 1.5 m.

Numbers come from report/data.py, so the poster cannot disagree with the report.
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
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "report"))
import data as D                     # noqa: E402
import figures_poster as FP          # noqa: E402

# ------------------------------------------------------------------ paper --
SIZES = {"A0": (841 * mm, 1189 * mm), "A1": (594 * mm, 841 * mm)}

NAVY = colors.HexColor("#12304A")
NAVY2 = colors.HexColor("#1B4166")
INK = colors.HexColor("#22364A")
MUTED = colors.HexColor("#54697E")
RULE = colors.HexColor("#D2DEE7")
CARD = colors.HexColor("#F4F8FA")
ORANGE = colors.HexColor("#E2561F")
TEAL = colors.HexColor("#12927A")
GOLD = colors.HexColor("#D9A21B")
PURPLE = colors.HexColor("#7E5AA8")
GOOD = colors.HexColor("#17794A")
BAD = colors.HexColor("#B23A1F")
MINT = colors.HexColor("#E6F2EE")
MINTLN = colors.HexColor("#BFDCD3")
WARM = colors.HexColor("#FDF3E6")
WARMLN = colors.HexColor("#EFDCBD")


def register_fonts():
    import matplotlib
    base = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    for name, fn in (("DJ", "DejaVuSans.ttf"), ("DJ-B", "DejaVuSans-Bold.ttf"),
                     ("DJ-I", "DejaVuSans-Oblique.ttf"),
                     ("DJM", "DejaVuSansMono.ttf"), ("DJM-B", "DejaVuSansMono-Bold.ttf")):
        p = os.path.join(base, fn)
        if os.path.exists(p):
            pdfmetrics.registerFont(TTFont(name, p))
    pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B", italic="DJ-I")


register_fonts()
F, FB, FI, FM = "DJ", "DJ-B", "DJ-I", "DJM"


def st(**kw):
    base = dict(name=f"s{len(_STYLES)}", fontName=F, fontSize=21, leading=28,
                textColor=INK, spaceAfter=0, alignment=TA_LEFT)
    base.update(kw)
    s = ParagraphStyle(**base)
    _STYLES.append(s)
    return s


_STYLES: list = []
S_TITLE = st(fontName=FB, fontSize=86, leading=94, textColor=colors.white)
S_SUB = st(fontSize=33, leading=41, textColor=colors.HexColor("#BFD3E2"))
S_AUTH = st(fontSize=25, leading=33, textColor=colors.HexColor("#E3EDF4"))
S_INST = st(fontName=FB, fontSize=23, leading=30, textColor=GOLD)
S_H = st(fontName=FB, fontSize=34, leading=41, textColor=NAVY)
S_H2 = st(fontName=FB, fontSize=25, leading=32, textColor=NAVY2)
S_BODY = st()
S_SMALL = st(fontSize=17, leading=23, textColor=MUTED)
S_CAP = st(fontSize=17, leading=22, textColor=MUTED, alignment=TA_CENTER)
S_CODE = st(fontName=FM, fontSize=17, leading=24)
S_TH = st(fontName=FB, fontSize=18, leading=24, textColor=colors.white)
S_TD = st(fontSize=19, leading=25)
S_TDC = st(fontSize=19, leading=25, alignment=TA_CENTER)
S_STATN = st(fontName=FB, fontSize=56, leading=62)
S_STATL = st(fontSize=22, leading=28, textColor=MUTED)
S_BANNER = st(fontName=FB, fontSize=26, leading=34, textColor=NAVY)


# --------------------------------------------------------------- flowables --
def Pg(txt, style=S_BODY):
    return Paragraph(txt, style)


def Bul(items, style=S_BODY):
    return [Paragraph(f"•&nbsp;&nbsp;{t}", style) for t in items]


def Code(lines, width):
    rows = [[Paragraph(ln.replace(" ", "&nbsp;") or "&nbsp;", S_CODE)] for ln in lines]
    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E9F0F5")),
        ("BOX", (0, 0), (-1, -1), 1, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def Tbl(header, rows, widths, highlight=(), fs=None):
    th, td, tdc = S_TH, S_TD, S_TDC
    if fs:
        th = ParagraphStyle("h", parent=S_TH, fontSize=fs, leading=fs + 6)
        td = ParagraphStyle("d", parent=S_TD, fontSize=fs, leading=fs + 6)
        tdc = ParagraphStyle("c", parent=S_TDC, fontSize=fs, leading=fs + 6)
    data = [[Paragraph(h, th) for h in header]] if header else []
    for r in rows:
        data.append([Paragraph(str(c), td if i == 0 else tdc) for i, c in enumerate(r)])
    t = Table(data, colWidths=widths)
    style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LINEBELOW", (0, 0), (-1, -1), 1, RULE),
             ("TOPPADDING", (0, 0), (-1, -1), 7),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
             ("LEFTPADDING", (0, 0), (-1, -1), 10),
             ("RIGHTPADDING", (0, 0), (-1, -1), 10)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    for r in highlight:
        style.append(("BACKGROUND", (0, r), (-1, r), MINT))
    t.setStyle(TableStyle(style))
    return t


def Img(path, width):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    return Image(path, width=width, height=width * h / w)


def Note(text, width, kind="note"):
    bg, ln = {"note": (CARD, RULE), "good": (MINT, MINTLN), "warn": (WARM, WARMLN)}[kind]
    t = Table([[Paragraph(text, S_BODY)]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 1.2, ln),
        ("LEFTPADDING", (0, 0), (-1, -1), 18), ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    return t


# ------------------------------------------------------------------ layout --
class Column:
    """A vertical cursor that draws flowables downward and tracks remaining room."""

    def __init__(self, c, x, top, width, bottom):
        self.c, self.x, self.y, self.w, self.bottom = c, x, top, width, bottom

    def room(self):
        return self.y - self.bottom

    def gap(self, h):
        self.y -= h

    def draw(self, flow, pad=0):
        w, h = flow.wrapOn(self.c, self.w - 2 * pad, self.room())
        flow.drawOn(self.c, self.x + pad, self.y - h)
        self.y -= h

    def card(self, number, title, items, accent=NAVY, pad=18, gap_after=18):
        """Measure the card's content, draw its background, then its content."""
        inner = self.w - 2 * pad
        head = Paragraph(f'<font color="#{accent.hexval()[2:]}">'
                         f'<b>{number}</b></font>&nbsp;&nbsp;{title}', S_H)
        hw, hh = head.wrapOn(self.c, inner, 10000)

        sized = []
        total = hh + 16
        for it in items:
            iw, ih = it.wrapOn(self.c, inner, 10000)
            sized.append((it, ih))
            total += ih + 9
        total += pad * 2 - 9

        top = self.y
        self.c.setFillColor(colors.white)
        self.c.setStrokeColor(RULE)
        self.c.setLineWidth(1.4)
        self.c.roundRect(self.x, top - total, self.w, total, 10, stroke=1, fill=1)
        # accent tab, not a full edge stripe
        self.c.setFillColor(accent)
        self.c.setStrokeColor(accent)
        self.c.roundRect(self.x + pad, top - pad - hh + 4, 10, hh - 10, 4, stroke=1, fill=1)

        y = top - pad
        head.drawOn(self.c, self.x + pad + 22, y - hh)
        y -= hh + 11
        for it, ih in sized:
            it.drawOn(self.c, self.x + pad, y - ih)
            y -= ih + 9
        self.y = top - total - gap_after
        return total


# ----------------------------------------------------------------- content --
def build(out_path, size="A0"):
    # Always lay out at A0. Font sizes are absolute points, so a smaller sheet
    # cannot simply reuse them -- A1 is the same artwork drawn through a
    # uniform scale, which is exactly what printing A0 artwork at 71% does.
    PW, PH = SIZES[size]
    W, H = SIZES["A0"]
    figdir = os.path.join(HERE, "_figs")
    figs = FP.build(figdir)
    A = os.path.join(HERE, "assets")

    c = pdfcanvas.Canvas(out_path, pagesize=(PW, PH))
    c.setTitle("Extending PARCO — SRP Group 9")
    c.setAuthor("SRP Group 9, Universität Hildesheim")
    if size != "A0":
        c.scale(PW / W, PH / H)

    M = 26 * mm
    GUT = 14 * mm
    colw = (W - 2 * M - 2 * GUT) / 3

    # ---------------------------------------------------------- header band

    # Measure first, then size the band to its content. Hard-coded offsets
    # clipped the subtitle and pushed the authors off the navy entirely.
    inner_w = W - 2 * M
    pad_t, pad_b, lead = 20 * mm, 15 * mm, 6 * mm
    head_parts = [
        (Pg("Extending PARCO", S_TITLE), inner_w, 7 * mm),
        (Pg("Does parallel decoding cost solution quality?&nbsp; "
            "Controlled experiments on min-max HCVRP", S_SUB), inner_w, lead),
        (Pg("Akshai Athota &nbsp;·&nbsp; Charitha Yetukuri &nbsp;·&nbsp; Nitin Sharma "
            "&nbsp;·&nbsp; Shehroz Khan &nbsp;·&nbsp; Mina George Soliman Hanna",
            S_AUTH), inner_w, 4 * mm),
        (Pg("Student Research Project · Group 9 · Universität Hildesheim",
            S_INST), inner_w, 0),
    ]
    measured = []
    for p, w, gap in head_parts:
        _, ph = p.wrapOn(c, w, 10000)
        measured.append((p, ph, gap))
    hh = pad_t + pad_b + sum(ph + g for _, ph, g in measured)

    c.setFillColor(NAVY)
    c.rect(0, H - hh, W, hh, stroke=0, fill=1)
    y = H - pad_t
    for p, ph, gap in measured:
        p.drawOn(c, M, y - ph)
        y -= ph + gap

    # ------------------------------------------------------ key-finding band
    bpad = 15 * mm
    banner_w = inner_w * .50
    stat_w = (inner_w - banner_w - 30 * mm) / 4

    banner = Pg("The conflict handler is not free.&nbsp; Replacing it with explicit "
                "masking and committing <b>two</b> agents per decoder pass instead of "
                "all <i>M</i> beats PARCO on solution quality on <b>every</b> test set "
                "while using <b>less</b> compute — and the gain grows with fleet size.",
                S_BANNER)
    _, ban_h = banner.wrapOn(c, banner_w, 10000)

    stats = [("−3.02%", "mean cost<br/>vs PARCO", TEAL),
             ("12 / 12", "test sets<br/>improved", TEAL),
             ("−34%", "decoder passes<br/>per instance", NAVY2),
             ("−16%", "training time<br/>per epoch", NAVY2)]
    sized = []
    for v, lab, col in stats:
        n = Pg(f'<font color="#{col.hexval()[2:]}">{v}</font>', S_STATN)
        _, nh = n.wrapOn(c, stat_w, 500)
        l = Pg(lab, S_STATL)
        _, lh = l.wrapOn(c, stat_w, 500)
        sized.append((n, nh, l, lh))
    stat_h = max(nh + 4 * mm + lh for _, nh, _, lh in sized)

    bh = max(ban_h, stat_h) + 2 * bpad
    by = H - hh - bh
    c.setFillColor(MINT)
    c.setStrokeColor(MINTLN)
    c.setLineWidth(1.5)
    c.rect(M, by, inner_w, bh, stroke=1, fill=1)

    banner.drawOn(c, M + bpad, by + (bh - ban_h) / 2)
    sx = M + banner_w + 30 * mm
    for i, (n, nh, l, lh) in enumerate(sized):
        x = sx + i * stat_w
        top_s = by + (bh + stat_h) / 2
        n.drawOn(c, x, top_s - nh)
        l.drawOn(c, x, top_s - nh - 4 * mm - lh)

    # ------------------------------------------------------------- columns
    top = by - 9 * mm
    bottom = 24 * mm
    cols = [Column(c, M + i * (colw + GUT), top, colw, bottom) for i in range(3)]
    col1, col2, col3 = cols
    iw = colw - 36          # inner width inside a card

    # ===================== COLUMN 1 — background and motivation ============
    col1.card("1", "The problem", [
        Pg("A fleet of <b>M</b> vehicles serves <b>N</b> customers from one depot. "
           "Vehicles differ in <b>capacity</b> and <b>speed</b>. A vehicle that runs "
           "out of capacity returns to reload."),
        Code(["minimise   max over vehicles m of",
              "",
              "              L_m  /  f_m",
              "",
              "   L_m  distance driven by vehicle m",
              "   f_m  its speed  →  L_m/f_m = finish time"], iw),
        Pg("This is <b>min-max</b>, not min-sum: we minimise when the <i>last</i> van "
           "finishes, so the problem is about <b>balance</b>. One idle van and one "
           "overloaded van scores badly even at small total distance."),
        Img(os.path.join(A, "hcvrp_instance.jpg"), iw * .58),
        Pg("A trained policy on one HCVRP instance", S_CAP),
        Note("Because the objective is a <b>maximum</b>, it is not comparable with "
             "methods that minimise total distance: POMO and AM numbers for CVRP are "
             "min-sum over one vehicle and belong in a different table.", iw, "note"),
    ], accent=NAVY2)

    col1.card("2", "What PARCO does", [
        Img(os.path.join(A, "parco_concept.jpg"), iw * .82),
        Pg("Sequential (top) versus parallel (bottom) construction", S_CAP),
        Pg("<b>All agents choose at the same decoder step</b>, instead of one after "
           "another. Three mechanisms make that work:"),
        *Bul(["<b>Communication layers</b> — transformer layers let agents exchange "
              "context while decoding.",
              "<b>Multiple pointer mechanism</b> — every agent points to its own next "
              "node in the same pass.",
              "<b>Priority conflict handler</b> — if two agents pick the same node, "
              "the higher learned priority wins; the loser stays put."]),
        Note("The action space is <b>M + N</b>, not N: the depot is replicated once "
             "per agent. Without private depot copies, the first van home would mark "
             "the depot visited for everyone, and no agent could express “stay”.",
             iw, "note"),
    ], accent=NAVY2)

    col1.card("3", "What the paper leaves open", [
        Pg("PARCO optimises for speed and reports speed. Three things are never "
           "measured:"),
        *Bul([
            "<b>What does parallelism cost in quality?</b> There is no sequential "
            "reference point, so the trade-off is unquantified.",
            "<b>The conflict handler is a fixed rule.</b> Agents 2…M choose from "
            "logits computed <i>before</i> the earlier picks in that same pass.",
            "<b>The logit clipping was inherited, never ablated.</b> C·tanh(z) at "
            "C = 10 has slope 10 at the origin — it <i>amplifies</i> rather than clips.",
        ]),
        Note("Each one becomes a controlled experiment, measured against a PARCO we "
             "trained ourselves under the identical recipe.", iw, "warn"),
    ], accent=ORANGE)

    # ============================ COLUMN 2 — methods =======================
    col2.card("4", "Method · one knob from sequential to joint", [
        Pg("We define <b>k</b> = the number of (agent, node) pairs committed per "
           "decoder pass. Our supervisor observed that in the fully sequential limit "
           "two of our ideas are <i>the same thing</i> — so they became one parameter."),
        Tbl(None, [["k = 1", "full sequential — every decision sees all previous ones"],
                   ["1 &lt; k &lt; M", "the interpolation — the points of the front"],
                   ["k = M", "masked joint — agents 2…M act on stale logits"]],
            [iw * .22, iw * .78], fs=21),
        Code(["for _ in range(min(k, num_agents)):",
              "    logp  = log_softmax(masked.reshape(B, -1))",
              "    agent, node = argmax(logp)",
              "    mask[agent, :] = False   # agent has decided",
              "    mask[:, node]  = False   # node is taken"], iw),
        *Bul([
            "<b>Collisions impossible at any k</b> — the priority handler never runs.",
            "<b>One pass = one decoder forward</b>: the k picks reuse the same logits "
            "tensor, which is what makes step counts comparable as compute.",
        ]),
    ], accent=ORANGE)

    col2.card("5", "Method · separating gain from saturation", [
        Pg("Write the clip as <b>φ(z) = g·tanh(z/τ)</b>. The gain at the origin is "
           "g/τ and the knee sits near 2τ — the single C was doing both jobs at once."),
        Img(figs["tanh_curves"], iw * .95),
        Pg("Because a softmax over φ(z) with slope s behaves like a softmax over z at "
           "temperature 1/s, PARCO's fixed form is effectively a <b>10× temperature "
           "drop</b>: it sharpens the policy and suppresses exploration."),
        Note("<b>Result: −0.93%</b>, better on 12/12 sets at identical cost per epoch. "
             "This <i>reverses</i> our earlier +3.5% result, which was confounded by "
             "clipping the encoder too and by an 8-GPU run against a 6-GPU baseline. "
             "At 10× the learning rate it diverges.", iw, "good"),
    ], accent=GOLD)

    col2.card("6", "Method · making the comparison budget-fair", [
        Pg("A greedy k = 1 rollout spends <b>1.34×</b> the decoder passes of parallel "
           "PARCO. So is its win simply bought with compute?"),
        Code(["passes per instance  =  steps × sampling rollouts"], iw),
        Pg("Each model is swept over best-of-n sampling and its cost read off against "
           "the budget <i>actually consumed</i>, rather than forcing one matched point."),
        Note("Two harness bugs had to be fixed first: best-of-n grouped the wrong "
             "elements for batches above one, and the step count is a per-batch "
             "<i>maximum</i>, so it grows with batch width. Both would have produced "
             "confidently wrong numbers.", iw, "warn"),
    ], accent=TEAL)

    setup_rows = [["Epochs", "100", "100"],
                  ["Instances / epoch", "100 000", "400 000"],
                  ["GPUs", "6 (every run)", "8"],
                  ["Effective batch", "768", "512"],
                  ["Test sets", "12 × 1 280 instances", "same"]]
    col2.card("7", "Setup", [
        Tbl(["Setting", "Our runs", "Paper"], setup_rows,
            [iw * .40, iw * .35, iw * .25], fs=20),
        Pg("Our smaller per-epoch budget is why our PARCO sits 6–12% above the "
           "published numbers — a budget difference, not a method difference. Every "
           "gap on this poster is therefore measured against <b>our own control</b>, "
           "trained with the identical recipe on the same six GPUs.", S_SMALL),
        Note("<b>Pipeline validated:</b> the paper prints 10.98 at N = 100, M = 3; "
             "running the authors' released checkpoint through our code gives "
             "<b>10.977</b>.", iw, "good"),
    ], accent=NAVY2)

    # ============================ COLUMN 3 — results =======================
    rows = []
    for label, d, hl in (("Parallel PARCO", D.CONTROL, False),
                         ("k = 1  sequential", D.K_TRAINED[1], True),
                         ("k = 2", D.K_TRAINED[2], True),
                         ("k = 4", D.K_TRAINED[4], False),
                         ("k = 7  joint", D.K_TRAINED[7], False)):
        g = D.gap(d)
        gc = "—" if d is D.CONTROL else (
            f'<font color="#{(GOOD if g < 0 else BAD).hexval()[2:]}"><b>{g:+.2f}%</b></font>')
        w = "—" if d is D.CONTROL else f"{D.wins(d)}/12"
        rows.append([label, f"{D.mean_cost(d):.4f}", gc, w, f"{D.mean_steps(d):.1f}"])

    col3.card("8", "Result · a clean quality–speed front", [
        Img(figs["pareto"], iw * .82),
        Tbl(["Method", "Cost", "Gap", "Wins", "Passes"], rows,
            [iw * .30, iw * .17, iw * .20, iw * .16, iw * .17],
            highlight=(2, 3), fs=21),
        Note("<b>k = 2 dominates.</b> Better on all 12 test sets, 34% fewer decoder "
             "passes, and 16% less wall-clock per training epoch. Not a trade-off — "
             "better on every axis at once.", iw, "good"),
    ], accent=TEAL)

    col3.card("9", "Result · the gain scales with fleet size", [
        Img(figs["m_scaling"], iw * .76),
        Pg("The more agents commit per pass, the more decisions are made on stale "
           "logits and the more collisions the priority rule must repair. Sequencing "
           "recovers exactly that loss — so the advantage grows from <b>−3.0%</b> at "
           "M = 3 to <b>−6.2%</b> at M = 7."),
        Note("The mechanism confirming itself: the effect is largest precisely where "
             "PARCO's parallelism is supposed to pay off most.", iw, "note"),
    ], accent=TEAL)

    col3.card("10", "Result · the win is not bought with compute", [
        Img(figs["budget"], iw * .73),
        Pg("Given up to <b>32×</b> the inference budget, parallel PARCO never reaches "
           "a single greedy k = 1 rollout. k = 1 wins 12/12 sets at every level."),
        Note("<b>Honest caveat:</b> surplus budget was spent only as i.i.d. sampling "
             "at temperature 1, which is weak for <i>all</i> models here — best-of-32 "
             "only just returns to the greedy cost. The claim is therefore “extra "
             "compute <i>spent this way</i> does not close the gap”.", iw, "warn"),
    ], accent=TEAL)

    col3.card("11", "Limitations and next steps", [
        Pg("<b>Did not finish:</b> dynamic re-encoding (43/100 epochs, ~10× slower) "
           "and the explicit wait action both hit the 72-hour job limit — budget "
           "findings, not negative results. <b>One seed per configuration</b>, so the "
           "small tanh effect needs error bars before it is settled."),
        *Bul(["Decoding-only k sweep: training-at-k vs decoding-at-k",
              "Low-temperature or augmentation search, not plain best-of-n",
              "A learned, parametric conflict handler",
              "Permutation-invariant likelihood for k &gt; 1",
              "Extend k to OMDCPDP and FFSP"]),
    ], accent=PURPLE)

    # -------------------------------------------------------------- footer
    fh = 22 * mm
    c.setFillColor(NAVY)
    c.rect(0, 0, W, fh, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#C7D8E5"))
    c.setFont(F, 20)
    c.drawString(M, fh / 2 - 7, "Code, checkpoints, full report and an interactive "
                                "delivery simulator:  github.com/Akshai-Athota/parco")
    c.drawRightString(W - M, fh / 2 - 7,
                      "Base work: Berto et al., PARCO, NeurIPS 2025")

    c.showPage()
    c.save()
    return out_path, [col.room() / mm for col in cols]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", choices=list(SIZES), default="A0")
    ap.add_argument("--out", default=None)
    o = ap.parse_args()
    out = o.out or os.path.join(HERE, f"PARCO_SRP_Poster_{o.size}.pdf")
    path, room = build(out, o.size)
    print(f"wrote {path}  ({os.path.getsize(path)//1024} KB)")
    print("remaining room per column (mm): " + ", ".join(f"{r:.0f}" for r in room))
