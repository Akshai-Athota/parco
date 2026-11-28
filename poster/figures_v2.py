"""Figures for the poster, in the reference poster's illustrated style.

The centrepiece is ``decoding()``: a drawn explanation of what PARCO does at a
decoder step versus what we do, in the same spirit as the reference poster's
matrix diagrams. Charts come second and are kept deliberately plain.

All numbers come from report/data.py.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
import numpy as np                                   # noqa: E402
from matplotlib.patches import FancyArrow, FancyBboxPatch, Rectangle  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "report"))
import data as D                                     # noqa: E402

NAVY = "#1F4E79"
INK = "#2B2B2B"
ORANGE = "#D9531E"
TEAL = "#0E8A72"
PURPLE = "#7E5AA8"
GREY = "#8C9AA6"
GOLD = "#C8911B"
MUTED = "#55616B"
DPI = 190

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 16,
    "axes.edgecolor": "#AFBECB", "axes.linewidth": 1.4,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": "#E4EAEF", "grid.linewidth": 1.2,
    "axes.axisbelow": True, "figure.facecolor": "white",
})


def _save(fig, out):
    fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


# --------------------------------------------------------------------------
# the centrepiece: one decoder step, PARCO versus ours
# --------------------------------------------------------------------------
def decoding(outdir):
    out = os.path.join(outdir, "v2_decoding.png")
    fig, axes = plt.subplots(2, 1, figsize=(13.0, 8.0))

    # a small joint logit grid: 3 agents x 6 candidate nodes
    vals = np.array([[0.2, 0.9, 0.3, 0.1, 0.4, 0.2],
                     [0.1, 0.8, 0.5, 0.2, 0.3, 0.1],
                     [0.3, 0.2, 0.4, 0.7, 0.2, 0.5]])
    agents = ["van 1", "van 2", "van 3"]
    nodes = ["depot", "A", "B", "C", "D", "E"]

    def grid(ax, x0, y0, cw, ch, highlight=(), masked=(), title="", tcol=INK):
        for r in range(3):
            for c in range(6):
                xy = (x0 + c * cw, y0 - (r + 1) * ch)
                is_hi = (r, c) in highlight
                is_ma = (r, c) in masked
                fc = "#FFFFFF"
                if is_ma:
                    fc = "#E4E8EB"
                if is_hi:
                    fc = "#FBD9C8" if highlight[(r, c)] == 1 else "#CCE8E0"
                ax.add_patch(Rectangle(xy, cw, ch, facecolor=fc,
                                       edgecolor="#6F7D88", lw=1.4, zorder=2))
                ax.text(xy[0] + cw / 2, xy[1] + ch / 2, f"{vals[r, c]:.1f}",
                        ha="center", va="center", fontsize=15, zorder=3,
                        color="#9AA6B0" if is_ma else INK,
                        fontweight="bold" if is_hi else "normal")
            ax.text(x0 - .12, y0 - (r + .5) * ch, agents[r], ha="right",
                    va="center", fontsize=14, color=MUTED)
        for c in range(6):
            ax.text(x0 + (c + .5) * cw, y0 + .06, nodes[c], ha="center",
                    va="bottom", fontsize=14, color=MUTED)
        if title:
            ax.text(x0 + 3 * cw, y0 + .42, title, ha="center", va="bottom",
                    fontsize=17, fontweight="bold", color=tcol)

    def arrow(ax, x, y, dx=0.5):
        ax.add_patch(FancyArrow(x, y, dx, 0, width=.012, head_width=.09,
                                head_length=.16, color="#5B6A76",
                                length_includes_head=True, zorder=4))

    cw, ch = .62, .55
    G1, G2, ANN = 1.0, 6.5, 10.55          # grid and annotation anchors

    def row(ax, side_label, side_col, t1, t2, hl1, hl2, mask2, note, tail=None):
        ax.set_xlim(-0.7, 13.4)
        ax.set_ylim(0.25, 3.45)
        ax.axis("off")
        ax.text(-0.35, 1.88, side_label, fontsize=23, fontweight="bold",
                color=side_col, ha="center", va="center", rotation=90)
        grid(ax, G1, 2.70, cw, ch, highlight=hl1, title=t1, tcol=side_col)
        arrow(ax, 5.05, 1.87, .40)
        grid(ax, G2, 2.70, cw, ch, highlight=hl2, masked=mask2, title=t2,
             tcol=side_col)
        ax.text(ANN, 2.45, note, fontsize=15, color=side_col, va="top",
                ha="left", linespacing=1.55)
        if tail:
            ax.text(ANN, 1.10, tail, fontsize=16, fontweight="bold",
                    color=side_col, va="top", ha="left")

    row(axes[0], "PARCO", ORANGE,
        "1 · all agents choose", "2 · van 2 is overruled",
        {(0, 1): 1, (1, 1): 1, (2, 3): 1}, {(0, 1): 1, (2, 3): 1}, {(1, 1)},
        "van 2 proposed node A,\nlost the tie and stays put —\nyet its gradient still\n"
        "credits a move that\nnever happened")

    row(axes[1], "Ours", TEAL,
        "1 · take the best pair", "2 · mask its row + column",
        {(0, 1): 2}, {(0, 1): 2},
        {(0, 0), (0, 2), (0, 3), (0, 4), (0, 5), (1, 1), (2, 1)},
        "no two agents can be given\nthe same node, so the\nconflict handler never runs",
        tail="repeat k times, then step")

    fig.subplots_adjust(hspace=.10)
    return _save(fig, out)


# --------------------------------------------------------------------------
def spectrum(outdir):
    """k as one dial from sequential to joint."""
    out = os.path.join(outdir, "v2_spectrum.png")
    fig, ax = plt.subplots(figsize=(13.0, 2.1))
    ax.set_xlim(0, 10)
    ax.set_ylim(0.52, 2.35)
    ax.axis("off")

    ax.add_patch(FancyBboxPatch((.4, 1.15), 9.2, .34,
                                boxstyle="round,pad=0.02,rounding_size=0.16",
                                facecolor="#E8EEF3", edgecolor="#B9C7D2", lw=1.4))
    stops = [(.95, "k = 1", "full sequential\nbest quality", ORANGE),
             (3.6, "k = 2", "our sweet spot\nbetter AND cheaper", TEAL),
             (6.3, "k = 4", "speed point", PURPLE),
             (9.0, "k = M", "masked joint\nfastest", GREY)]
    for x, lab, sub, col in stops:
        ax.add_patch(plt.Circle((x, 1.32), .17, facecolor=col, edgecolor="white",
                                lw=2.4, zorder=3))
        ax.text(x, 1.78, lab, ha="center", fontsize=19, fontweight="bold", color=col)
        ax.text(x, 1.02, sub, ha="center", va="top", fontsize=14.5, color=MUTED,
                linespacing=1.45)
    ax.annotate("", xy=(9.45, 1.32), xytext=(.55, 1.32),
                arrowprops=dict(arrowstyle="-|>", lw=1.6, color="#9AABB8"))
    return _save(fig, out)


# --------------------------------------------------------------------------
def pareto(outdir):
    out = os.path.join(outdir, "v2_pareto.png")
    fig, ax = plt.subplots(figsize=(9.6, 6.4))
    pts = [("Parallel PARCO", D.mean_steps(D.CONTROL), D.mean_cost(D.CONTROL), NAVY)]
    for k, col in ((1, ORANGE), (2, TEAL), (4, PURPLE), (7, GREY)):
        d = D.K_TRAINED[k]
        pts.append((f"k = {k}", D.mean_steps(d), D.mean_cost(d), col))

    kx, ky = D.mean_steps(D.K_TRAINED[2]), D.mean_cost(D.K_TRAINED[2])
    ax.add_patch(Rectangle((kx, ky), 104 - kx, 6.55 - ky, facecolor=TEAL,
                           alpha=.08, edgecolor="none", zorder=0))
    ax.text(101, 6.50, "slower and worse\nthan k = 2", fontsize=15, color=TEAL,
            fontweight="bold", ha="right", va="top", linespacing=1.35)

    ax.plot([p[1] for p in pts[1:]], [p[2] for p in pts[1:]], "-",
            color="#B3C2CE", lw=3.0, zorder=1)
    off = {"Parallel PARCO": (0, 26), "k = 7": (0, 24), "k = 4": (0, 24),
           "k = 2": (0, -42), "k = 1": (0, 24)}
    for label, x, y, col in pts:
        ax.scatter([x], [y], s=400, color=col, zorder=3, edgecolor="white", lw=3)
        ax.annotate(label, (x, y), textcoords="offset points", xytext=off[label],
                    ha="center", fontsize=17, color=col, fontweight="bold")
    ax.axhline(D.mean_cost(D.CONTROL), color=NAVY, ls=":", lw=2.0, zorder=0)
    ax.set_xlabel("decoder passes per instance  (lower = faster)", fontsize=16)
    ax.set_ylabel("mean cost, 12 test sets  (lower = better)", fontsize=16)
    ax.set_xlim(8, 104)
    ax.set_ylim(5.80, 6.55)
    ax.tick_params(labelsize=15)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _save(fig, out)


# --------------------------------------------------------------------------
def scaling(outdir):
    out = os.path.join(outdir, "v2_scaling.png")
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ms = [3, 5, 7]
    width = .34
    for i, (k, col) in enumerate(((1, ORANGE), (2, TEAL))):
        vals = [D.gap_by_m(D.K_TRAINED[k], m) for m in ms]
        xs = np.arange(len(ms)) + (i - .5) * width
        ax.bar(xs, vals, width, color=col, label=f"k = {k}")
        for x, v in zip(xs, vals):
            ax.annotate(f"{v:.1f}%", (x, v), ha="center", va="top", fontsize=15,
                        color=MUTED, xytext=(0, -6), textcoords="offset points")
    ax.axhline(0, color=NAVY, lw=1.8)
    ax.set_xticks(range(len(ms)))
    ax.set_xticklabels([f"M = {m}" for m in ms], fontsize=16)
    ax.set_ylabel("cost gap vs PARCO (%)", fontsize=16)
    ax.set_ylim(-7.6, .6)
    ax.tick_params(labelsize=15)
    ax.legend(frameon=False, ncol=2, fontsize=16, loc="lower left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _save(fig, out)


ALL = [decoding, spectrum, pareto, scaling]


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    return {fn.__name__: fn(outdir) for fn in ALL}


if __name__ == "__main__":
    o = sys.argv[1] if len(sys.argv) > 1 else "_figs_v2"
    for n, p in build(o).items():
        print(f"  {n:11} {p}")
