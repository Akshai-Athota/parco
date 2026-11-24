"""Charts sized and weighted for an A0 poster.

Separate from report/figures.py on purpose: a poster is read from a metre away,
so line weights, marker sizes and fonts are all heavier. The data comes from
the same module, so the numbers cannot diverge from the report.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt              # noqa: E402
import numpy as np                           # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "report"))
import data as D                             # noqa: E402

NAVY, ORANGE, TEAL, GOLD, PURPLE, GREY = (
    "#12304A", "#E2561F", "#12927A", "#D9A21B", "#7E5AA8", "#8296A6")
MUTED = "#4A6075"
DPI = 190

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 19,
    "axes.edgecolor": "#B9C8D4", "axes.linewidth": 1.6,
    "axes.labelcolor": MUTED, "axes.labelsize": 19,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 18, "ytick.labelsize": 18,
    "axes.grid": True, "grid.color": "#E3EAF0", "grid.linewidth": 1.4,
    "axes.axisbelow": True, "figure.facecolor": "white",
    "legend.fontsize": 18,
})


def _finish(fig, axes, out):
    for ax in (axes if isinstance(axes, (list, tuple, np.ndarray)) else [axes]):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return out


def pareto(outdir):
    out = os.path.join(outdir, "p_pareto.png")
    fig, ax = plt.subplots(figsize=(11.0, 7.4))
    pts = [("Parallel PARCO", D.mean_steps(D.CONTROL), D.mean_cost(D.CONTROL), NAVY)]
    for k, col in ((1, ORANGE), (2, TEAL), (4, PURPLE), (7, GREY)):
        d = D.K_TRAINED[k]
        pts.append((f"k = {k}", D.mean_steps(d), D.mean_cost(d), col))

    # everything up-and-right of k = 2 is worse on both axes at once
    from matplotlib.patches import Rectangle
    kx, ky = D.mean_steps(D.K_TRAINED[2]), D.mean_cost(D.K_TRAINED[2])
    ax.add_patch(Rectangle((kx, ky), 102 - kx, 6.52 - ky, facecolor=TEAL,
                           alpha=.085, edgecolor="none", zorder=0))
    ax.annotate("slower and worse\nthan k = 2", (99, 6.47), fontsize=18,
                color=TEAL, fontweight="bold", ha="right", va="top",
                linespacing=1.35)

    ax.plot([p[1] for p in pts[1:]], [p[2] for p in pts[1:]],
            "-", color="#AFC0CD", lw=3.4, zorder=1)
    offsets = {"Parallel PARCO": (0, 34), "k = 7": (0, 32), "k = 4": (0, 32),
               "k = 2": (0, -52), "k = 1": (0, 32)}
    for label, x, y, col in pts:
        ax.scatter([x], [y], s=620, color=col, zorder=3, edgecolor="white", lw=4)
        ax.annotate(label, (x, y), textcoords="offset points",
                    xytext=offsets[label], ha="center", fontsize=21,
                    color=col, fontweight="bold")

    ctrl = D.mean_cost(D.CONTROL)
    ax.axhline(ctrl, color=NAVY, ls=":", lw=2.4, zorder=0)

    ax.set_xlabel("decoder passes per instance   (lower = faster)")
    ax.set_ylabel("mean cost over 12 test sets   (lower = better)")
    ax.set_xlim(8, 102)
    ax.set_ylim(5.78, 6.52)
    return _finish(fig, ax, out)


def m_scaling(outdir):
    out = os.path.join(outdir, "p_mscaling.png")
    fig, ax = plt.subplots(figsize=(11.0, 6.2))
    ms = [3, 5, 7]
    width = .2
    for i, (k, col) in enumerate(((1, ORANGE), (2, TEAL), (4, PURPLE), (7, GREY))):
        vals = [D.gap_by_m(D.K_TRAINED[k], m) for m in ms]
        xs = np.arange(len(ms)) + (i - 1.5) * width
        ax.bar(xs, vals, width, color=col, label=f"k = {k}")
        for x, v in zip(xs, vals):
            ax.annotate(f"{v:+.1f}", (x, v), ha="center", fontsize=16, color=MUTED,
                        va="bottom" if v > 0 else "top",
                        xytext=(0, 4 if v > 0 else -6), textcoords="offset points")
    ax.axhline(0, color=NAVY, lw=2.2)
    ax.set_xticks(range(len(ms)))
    ax.set_xticklabels([f"M = {m} vehicles" for m in ms])
    ax.set_ylabel("cost gap vs parallel PARCO (%)")
    ax.set_ylim(-8.6, 8.6)
    ax.legend(frameon=False, ncol=4, loc="upper left")
    return _finish(fig, ax, out)


def tanh_curves(outdir):
    out = os.path.join(outdir, "p_tanh.png")
    z = np.linspace(-12, 12, 600)
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.9))
    axes[0].plot(z, 10 * np.tanh(z), color=GOLD, lw=4.2, label=r"$10\tanh(z)$  PARCO")
    axes[0].plot(z, 10 * np.tanh(z / 10), color=TEAL, lw=4.2, label=r"$10\tanh(z/10)$  scaled")
    axes[0].plot(z, z, color="#C3CED7", lw=2.2, ls="--", label="identity")
    axes[0].set_ylim(-12, 12)
    axes[0].set_title(r"$\varphi(z)=g\tanh(z/\tau)$", fontsize=21, color=NAVY, pad=12)
    axes[0].legend(frameon=False, fontsize=16, loc="upper left")

    axes[1].plot(z, 10 / np.cosh(z) ** 2, color=GOLD, lw=4.2)
    axes[1].plot(z, 1 / np.cosh(z / 10) ** 2, color=TEAL, lw=4.2)
    axes[1].axhline(1, color="#C3CED7", lw=2.2, ls="--")
    axes[1].set_title("slope at the origin:  10  vs  1", fontsize=21, color=NAVY, pad=12)
    axes[1].annotate("amplifies", (0.4, 8.6), fontsize=18, color=GOLD, fontweight="bold")
    axes[1].annotate("near-identity", (3.0, 1.7), fontsize=18, color=TEAL, fontweight="bold")
    for ax in axes:
        ax.set_xlabel("logit  z", fontsize=18)
    return _finish(fig, axes, out)


def budget(outdir):
    out = os.path.join(outdir, "p_budget.png")
    fig, ax = plt.subplots(figsize=(11.0, 6.0))
    mults = D.EQUAL_BUDGET["mults"]
    for key, col, lab in (("parallel", NAVY, "Parallel PARCO"), ("k1", ORANGE, "k = 1"),
                          ("k2", TEAL, "k = 2"), ("k4", PURPLE, "k = 4"),
                          ("k7", GREY, "k = 7")):
        ax.plot(mults, D.EQUAL_BUDGET["rows"][key], "o-", color=col, lw=3.4, ms=11,
                label=lab)
    ax.set_xscale("log")
    # a log axis adds its own minor ticks, which crowd the labels at poster size
    from matplotlib.ticker import NullLocator
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticks(mults)
    ax.set_xticklabels([f"{m:g}×" for m in mults])
    ax.set_xlabel("inference budget  (× one greedy parallel-PARCO rollout)")
    ax.set_ylabel("best cost within budget")
    ax.set_ylim(5.72, 6.72)
    ax.legend(frameon=False, ncol=5, loc="upper center",
              bbox_to_anchor=(.5, 1.03), columnspacing=1.1, handlelength=1.5)
    return _finish(fig, ax, out)


ALL = [pareto, m_scaling, tanh_curves, budget]


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    return {fn.__name__: fn(outdir) for fn in ALL}


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "_figs"
    for n, p in build(out).items():
        print(f"  {n:12} {p}")
