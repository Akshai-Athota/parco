"""Deck-specific charts: how the work scales as k changes.

The headline analysis here is derived, not just reported. Passes fall with k,
but sublinearly: an episode can never be shorter than the busiest vehicle's own
trajectory, and agents that have finished or are capacity-blocked cannot take a
slot in a pass. So the realised parallelism saturates, and that is precisely why
k = 2 is the sweet spot.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data as D                         # noqa: E402

NAVY, ORANGE, TEAL, PURPLE, GREY = "#12304A", "#E2561F", "#12927A", "#7E5AA8", "#8296A6"
MUTED = "#5B7085"
DPI = 200

# wall-clock seconds per training epoch, from the run logs
EPOCH_S = {"par": 603, 1: 711, 2: 508, 4: 351, 7: 340}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": "#C2CFD9", "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": "#E7EDF2", "grid.linewidth": .9,
    "axes.axisbelow": True, "figure.facecolor": "white",
})

KS = (1, 2, 4, 7)


def _fin(fig, axes, out):
    for ax in (axes if isinstance(axes, (list, tuple, np.ndarray)) else [axes]):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return out


def passes_vs_k(outdir):
    """Measured passes against the ideal 1/k curve: the gap is the saturation."""
    out = os.path.join(outdir, "d_passes.png")
    p1 = D.mean_steps(D.K_TRAINED[1])
    meas = [D.mean_steps(D.K_TRAINED[k]) for k in KS]
    ideal = [p1 / k for k in KS]

    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.plot(KS, ideal, "--", color="#A9BBC8", lw=2.2, label="ideal  (passes = 85.5 / k)")
    ax.plot(KS, meas, "o-", color=NAVY, lw=2.6, ms=9, label="measured")
    for k, m, i in zip(KS, meas, ideal):
        ax.annotate(f"{m:.1f}", (k, m), textcoords="offset points", xytext=(0, 11),
                    ha="center", fontsize=11, color=NAVY, fontweight="bold")
        if k >= 4:
            ax.annotate("", xy=(k, m), xytext=(k, i),
                        arrowprops=dict(arrowstyle="<->", color=ORANGE, lw=1.6))
    ax.annotate("the gap is work that\ncannot be parallelised",
                xy=(6.85, 15.5), xytext=(3.15, 8),
                fontsize=10.5, color=ORANGE, ha="center", va="center",
                linespacing=1.4,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.4,
                                connectionstyle="arc3,rad=.18"))
    ax.axhline(D.mean_steps(D.CONTROL), color=TEAL, ls=":", lw=1.8)
    ax.annotate("parallel PARCO (65.6)", (6.9, 68), fontsize=10, color=TEAL, ha="right")
    ax.set_xticks(KS)
    ax.set_xlabel("k  (pairs committed per decoder pass)")
    ax.set_ylabel("decoder passes per instance")
    ax.set_ylim(0, 95)
    ax.legend(frameon=False, fontsize=10.5, loc="upper right")
    return _fin(fig, ax, out)


def efficiency(outdir):
    """How much of the theoretical k-fold speedup is actually realised."""
    out = os.path.join(outdir, "d_efficiency.png")
    p1 = D.mean_steps(D.K_TRAINED[1])
    eff = [100 * (p1 / D.mean_steps(D.K_TRAINED[k])) / k for k in KS]
    cols = [ORANGE, TEAL, PURPLE, GREY]

    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    bars = ax.bar([str(k) for k in KS], eff, color=cols, width=.58)
    for b, e in zip(bars, eff):
        ax.annotate(f"{e:.0f}%", (b.get_x() + b.get_width() / 2, e),
                    textcoords="offset points", xytext=(0, 5), ha="center",
                    fontsize=13, fontweight="bold", color=MUTED)
    ax.axhline(100, color="#A9BBC8", ls="--", lw=1.8)
    ax.set_xlabel("k")
    ax.set_ylabel("realised share of the\ntheoretical k× speedup")
    ax.set_ylim(0, 118)
    ax.set_yticks([0, 25, 50, 75, 100])
    return _fin(fig, ax, out)


def cost_of_speed(outdir):
    """Pair the speedup with what it costs in quality -- the whole argument."""
    out = os.path.join(outdir, "d_tradeoff.png")
    p1 = D.mean_steps(D.K_TRAINED[1])
    speed = [p1 / D.mean_steps(D.K_TRAINED[k]) for k in KS]
    gap = [D.gap(D.K_TRAINED[k]) for k in KS]

    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    ax2 = ax.twinx()
    x = np.arange(len(KS))
    ax.bar(x - .19, speed, .38, color=NAVY, label="speedup vs k = 1")
    ax2.bar(x + .19, gap, .38, color=ORANGE, label="cost gap vs PARCO (%)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"k = {k}" for k in KS])
    ax.set_ylabel("decoder-pass speedup\nover k = 1", color=NAVY)
    ax2.set_ylabel("cost gap vs PARCO (%)", color=ORANGE)
    ax.tick_params(axis="y", colors=NAVY)
    ax2.tick_params(axis="y", colors=ORANGE)
    ax.set_ylim(0, 5.2)
    ax2.set_ylim(-6.5, 6.5)
    ax2.axhline(0, color=MUTED, lw=1.2)
    ax2.grid(False)
    for xi, (s, g) in enumerate(zip(speed, gap)):
        ax.annotate(f"{s:.1f}×", (xi - .19, s), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=10.5, color=NAVY,
                    fontweight="bold")
        ax2.annotate(f"{g:+.1f}", (xi + .19, g), textcoords="offset points",
                     xytext=(0, 5 if g > 0 else -13), ha="center", fontsize=10.5,
                     color=ORANGE, fontweight="bold")
    ax.spines[["top"]].set_visible(False)
    ax2.spines[["top"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return out


ALL = [passes_vs_k, efficiency, cost_of_speed]


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    return {fn.__name__: fn(outdir) for fn in ALL}


if __name__ == "__main__":
    o = sys.argv[1] if len(sys.argv) > 1 else "_figs_deck"
    for n, p in build(o).items():
        print(f"  {n:14} {p}")
